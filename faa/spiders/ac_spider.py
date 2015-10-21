from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider, Request, Rule, CrawlSpider
from datetime import datetime
from scrapy.selector import Selector
from faa.items import FaaDocItem
import pdb
import re
import os
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from faa import settings
import smtplib
from email.mime.text import MIMEText
from win32com.client.gencache import EnsureDispatch
from win32com.client import constants
from email.mime.text import MIMEText

doc_id_regex = re.compile('.*\/documentID\/(\w*\d*)\/?')

def load_xpaths():
    xpaths = {
        'relevant': '',
        'number': './/td[1]/text()',
        'office_name': '',
        'office_subname': '',
        'office_acronym': '//*[@id="content"]/table/tbody/tr/td[2]/text()',
        'office_page_link': './/td[2]/a/@href',
        'title': './/td[3]/a/text()',
        'date': './/td[4]/text()',
        'document_id': '',
        'document_link': '',
        'document_page_link': './/td[3]/a/@href',
        'output_folder': '',
        'updated': ''
    }

    return xpaths


def build_sublink(link_suffix):
    return 'https://www.faa.gov{}'.format(link_suffix)


class AcSpider(CrawlSpider):
    name = 'ac'
    allowed_domains = [r'www.faa.gov']
    start_urls = [
        r'https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.list'
    ]
    rules = (
        # link to get document pdf
        Rule(
            LinkExtractor(allow=('.*/documentID/.*',)),
            callback="parse_document_page",
            ),
        # next page button
        Rule(
            LinkExtractor(restrict_xpaths=['//ul[@class="pagination join"]/li/a[contains(text(), "Next")]']),
            follow=True,
            callback="parse_start_url"
            ),
    )

    def __init__(self, *args, **kwargs):
        super(AcSpider, self).__init__(*args, **kwargs)
        self.name = 'ac'
        self.item_xpaths = load_xpaths()
        self.current_data = {}
        self.document_file = settings.AC_DOCUMENT_FILE
        self.headers = settings.AC_HEADERS
        self.relevant_offices = {office.split(',')[0].strip(): office.split(',')[1].strip() for office in open(settings.RELEVANT_OFFICE_FILE)}
        self.items = []
        self.updated = 0
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def parse_start_url(self, response):

        sel = Selector(response)
        for row in sel.xpath(r'//*[@id="content"]/table/tbody/tr'):
            item = FaaDocItem()
            for name, path in self.item_xpaths.iteritems():
                try:
                    item[name] = row.xpath(path).extract()[0].strip().replace(',', '')
                except (KeyError, IndexError, ValueError):
                    item[name] = ''
            item['document_page_link'] = build_sublink(item['document_page_link'])
            item['document_id'] = doc_id_regex.search(item['document_page_link']).groups()[0]
            item['title'] = item['title'].replace('/', '_')
            item['number'] = item['number'].replace('/', '_')
            # check if newer on faa site
            if not self.current_data.get(item['document_id']):
                self.current_data[item['document_id']] = item['date']
            if item['date'] > self.current_data.get(item['document_id']):
                self.updated += 1
                item['updated'] = True
            else:
                item['updated'] = False
            yield Request(item['document_page_link'], callback=self.process_document_page, meta={'item': item})

    def process_document_page(self, response):
        sel = Selector(response)
        item = response.meta['item']
        try:
            office_name = sel.xpath('//dt[contains(text(), "Responsible Office")]/following-sibling::dd/a/text()').extract()[0]
        except IndexError:
            try:
                office_name = sel.xpath('//dt[contains(text(), "Responsible Office")]/following-sibling::dd/text()').extract()[0]
            except IndexError:
                office_name = item['office_acronym']
                if office_name == '':
                    office_name = 'misc'
        if ', ' and ' - ' in office_name:
            office_name = office_name.split(',')
            office_acronym = office_name[0].strip()
            office_name = office_name[1].split(' - ')
            office_subname = office_name[1].strip()
            office_name = office_name[0].strip()
        elif len(office_name.split(',')) == 3:
            office_name = office_name.split(',')
            office_acronym = office_name[0].strip()
            office_subname = office_name[2].strip()
            office_name = office_name[1].strip()
        elif len(office_name.split(',')) == 2:
            office_name = office_name.split(',')
            office_acronym = office_name[0].strip()
            office_name = office_name[1].strip()
            office_subname = ''
        else:
            office_subname = ''
            office_acronym = office_name

        if item['office_acronym'] == '':
            item['office_acronym'] = office_acronym
        item['office_subname'] = office_subname
        item['office_name'] = office_name

        for office, output_name in self.relevant_offices.iteritems():
            if office.lower() in item['office_name'].lower():
                item['output_folder'] = os.path.join(settings.AC_DOCUMENT_FOLDER, output_name)
                item['relevant'] = True
                break
            else:
                item['relevant'] = False
        try:
            item['document_link'] = sel.xpath('//*[@id="content"]/div/ul/li/a/@href').extract()[0]
        except IndexError:
            item['document_link'] = ''
        self.items.append(item)
        yield item

    def send_mail_via_smtp(self):
        username = 'kbonnet_cwec@yahoo.com' #os.environ['YAHOO_USERNAME'] + '@yahoo.com'
        password = 'vOgel1234' #os.environ['YAHOO_PASSWORD']

        updated = [item for item in self.items if item['updated'] is True]
        if len(updated) == 0:  # final check for updated data
            return None
        address_book = {line.split(',')[0].strip(): line.split(',')[1].strip() for line in open(settings.ADDRESS_BOOK_FILE)}
        recipients_names = [recipient.strip() for recipient in open(settings.RECIPIENT_FILE)]
        recipients_emails = [address_book[name] for name in recipients_names if name in address_book]

        fp = open(settings.EMAIL_TEMPLATE_AC_FILE, 'rb')
        body = fp.read()

        for i in updated:
            body += '> {0}: {1} \n\tupdated on {2}\n'.format(i['number'].encode('utf-8'), i['title'].encode('utf-8'), i['date'])

        body += '''
        \n\n
This bot searches www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.list every morning and
downloads the latest ACs from relevant FAA offices to the server location above. This email is only generated if
updated documents are found.

Reply to be removed from this list.

Kyle Bonnet
        '''
        msg = MIMEText(body)
        msg['Subject'] = 'Updates to FAA guidance'
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
        with open(settings.AC_DOCUMENT_FILE) as f:
            for row in f:
                try:
                    row = row.strip().split(',')
                    self.current_data[row[0]] = row[1]
                except:
                    continue

    def spider_closed(self, spider):
        if len(self.items) > 0:
            with open(self.document_file, 'w') as f:
                for item in self.items:
                    for header in self.headers:
                        f.write('{},'.format(item[header]))
                    f.write('\n')
        if self.updated > 0:
            # self.send_email()
            self.send_mail_via_smtp()







#
#     def send_mail_via_com(self):
#         updated = [item for item in self.items if item['updated'] is True]
#         if len(updated) == 0:  # final check for updated data
#             return None
#         address_book = {line.split(',')[0].strip(): line.split(',')[1].strip() for line in open(settings.ADDRESS_BOOK_FILE)}
#         recipients_names = [recipient.strip() for recipient in open(settings.RECIPIENT_FILE)]
#         recipients_emails = [address_book[name] for name in recipients_names if name in address_book]
#
#         o = EnsureDispatch("Outlook.Application")
#
#         fp = open(settings.EMAIL_TEMPLATE_AC_FILE, 'rb')
#         body = fp.read()
#
#         for i in updated:
#             body += '> {}: {} \n\tupdated on {}\n'.format(i['number'].encode('utf-8'), i['title'].encode('utf-8'), i['date'])
#
#         body += '''
#         \n\n
# This bot searches www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.list every morning and
# downloads the latest ACs from relevant FAA offices to the server location above. This email is generated if
# updated documents are found. To suggest an AC, reply with the AC number or title and I will include it in the search.
# Reply to be removed from this list.
#
# Kyle Bonnet
#         '''
#         Msg = o.CreateItem(constants.olMailItem)
#         for email in recipients_emails:
#             to = Msg.Recipients.Add(email)
#         to.Type = constants.olTo
#         Msg.Sender = 'Kyle Bonnet'
#         Msg.Recipients.ResolveAll()
#         Msg.Subject = 'Updated AC Documents Identified --TEST--'
#         Msg.Body = body
#
#         Msg.Send()
#         print '{0} EMAIL SENT {0}'.format('*' * 10)