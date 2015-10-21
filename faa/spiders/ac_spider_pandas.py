import re
import os
import smtplib
from email.mime.text import MIMEText

from scrapy.spiders import Request, CrawlSpider
from scrapy.selector import Selector
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import pandas as pd
import numpy as np
from requests.structures import CaseInsensitiveDict


from faa.items import FaaDocItem
from faa import settings
from datetime import datetime


doc_id_regex = re.compile('.*\/documentID\/([\w\d]*)\/?')


def item_search_link(search_term):
    return 'https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.list?omni=ACs&q={}&display=current&parentTopicID=0&documentNumber='.format(search_term)


def faa_link(sublink):
    return 'https://www.faa.gov/{}'.format(sublink)


class AcSpiderPandas(CrawlSpider):
    name = 'acp'
    allowed_domains = [r'www.faa.gov']
    start_urls = [
        r'https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.list/parentTopicID/0/display/current/changeNumber/0/layoutTemplate/excel/sortResults/false/sortColumn/dateIssued/sortOrder/DESC'
    ]

    def __init__(self, *args, **kwargs):
        super(AcSpiderPandas, self).__init__(*args, **kwargs)
        self.name = 'ac'
        self.current_data = {}
        self.document_file = settings.AC_DOCUMENT_FILE
        self.headers = settings.AC_HEADERS
        self.relevant_offices = CaseInsensitiveDict({office.split(',')[0].strip(): office.split(',')[1].strip() for office in open(settings.RELEVANT_OFFICE_FILE)})
        self.updated_items = []
        # self.items = []
        self.ac_frame = None
        self.updated = 0
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def parse_start_url(self, response):
        self.ac_frame = pd.read_html(response.url)[0]
        self.ac_frame.columns = self.ac_frame.columns.map(lambda x: x.lower())
        # convert date column to dateitme objects
        self.ac_frame['date'] = pd.to_datetime(self.ac_frame['date'], format='%m-%d-%Y')
        # replace '/' in number with '%2F for search query building and '/' for '_' for file naming
        self.ac_frame['search_number'] = self.ac_frame['number'].map(lambda x: x.replace('/', '%2F'))
        self.ac_frame['file_number'] = self.ac_frame['number'].map(lambda x: x.replace('/', '_'))
        self.ac_frame['document_id'] = np.nan
        for index, row in self.ac_frame.iterrows():
            item = FaaDocItem()
            item['row'] = row
            search_url = item_search_link(item['row']['search_number'])

            # yield a request that searches for document with doc number
            yield Request(search_url, callback=self.process_search_result_page, meta={'item': item})

    def process_search_result_page(self, response):
        sel = Selector(response)
        item = response.meta['item']
        item['row']['url'] = faa_link(sel.xpath('//*[@id="content"]/table/tbody/tr/td[3]/a/@href').extract()[0])
        yield Request(item['row']['url'], callback=self.process_document_page, meta={'item': item})

    def process_document_page(self, response):
        sel = Selector(response)
        item = response.meta['item']
        item['row']['document_id'] = doc_id_regex.search(response.url).groups()[0]

        try:
            self.ac_frame.loc[self.ac_frame['number'] == item['row']['number'], 'document_id'] = item['row']['document_id']
        except:
            pass


        try:
            sub_folder = item['row']['office'][:item['row']['office'].index('-')]
        except:
            sub_folder = ''

        try:
            item['row']['document_link'] = sel.xpath('//*[@id="content"]/div/ul/li/a/@href').extract()[0]
        except IndexError:
            item['row']['document_link'] = ''

        try:
            office_bool = item['row']['office'] in self.relevant_offices
        except:
            office_bool = False
        if office_bool:
            item['row']['relevant'] = True
            item['row']['output_folder'] = os.path.join(settings.AC_DOCUMENT_FOLDER, self.relevant_offices[item['row']['office']])

        else:
            item['row']['relevant'] = False
            item['row']['output_folder'] = os.path.join(settings.AC_DOCUMENT_FOLDER, 'Other', sub_folder, item['row']['office'])

        yield item

    def send_mail_via_smtp(self):
        username = os.environ['YAHOO_USERNAME'] + '@yahoo.com'
        password = os.environ['YAHOO_PASSWORD']

        updated = sorted([item for item in self.updated_items], key=lambda k: k['row']['date'], reverse=True)
        address_book = {line.split(',')[0].strip(): line.split(',')[1].strip() for line in open(settings.ADDRESS_BOOK_FILE)}
        recipients_names = [recipient.strip() for recipient in open(settings.RECIPIENT_FILE)]
        recipients_emails = [address_book[name] for name in recipients_names if name in address_book]

        fp = open(settings.EMAIL_TEMPLATE_AC_FILE, 'rb')
        body = fp.read()

        for i in updated:
            body += '  > {0}: {1} \n\tupdated on {2}\n'.format(i['row']['number'].encode('utf-8'), i['row']['title'].encode('utf-8'), i['row']['date'].strftime('%b-%d-%Y'))
        body += '''
        \n\n
  This bot searches www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.list every morning and
  downloads the latest ACs from relevant FAA offices to the server location above. This email is only generated if
  updated documents are found.

  Reply to be removed from this list.

  Kyle Bonnet
        '''
        msg = MIMEText(body)
        msg['Subject'] = 'TEST EMAIL: Updates to FAA guidance'
        msg['From'] = 'Kyle Bonnet'
        msg['To'] = ','.join(recipients_names)

        try:
            smtpserver = smtplib.SMTP("smtp.mail.yahoo.com", 587)
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo()
            smtpserver.login(username, password)
            fromaddr = username
            smtpserver.sendmail(fromaddr, recipients_emails, msg.as_string())
            print '{0} EMAIL SENT {0}'.format('*' * 10)
        except Exception as e:
            print "failed to send mail"
            print e

    def spider_opened(self, spider):
        if os.path.isfile(self.document_file) and os.path.getsize(self.document_file) > 0:
            with open(self.document_file) as f:
                for row in f:
                    try:
                        row = row.strip().split(',')
                        self.current_data[row[0]] = pd.to_datetime(row[1], format='%Y-%m-%d')
                    except:
                        continue
        else:
            open(self.document_file, 'wb').close()
            self.current_data = None

    def spider_closed(self, spider):
        with open(self.document_file, 'w') as f:
            for index, ac in self.ac_frame.iterrows():
                pass
                f.write('{},{}\n'.format(ac['document_id'], ac['date'].date()))
        if self.updated > 0:
            self.send_mail_via_smtp()

# todo: add ac_subsets as next layer in folders
# todo: catch depricated ac (i.e. 150/2350-10B supersedes 150/2350-10A)