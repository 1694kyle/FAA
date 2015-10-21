# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import urllib2
import os
from scrapy.exceptions import DropItem


class InitialPipeline(object):
    def process_item(self, item, spider):
        return item


class UpdatedPipeline(object):
    def process_item(self, item, spider):
        if spider.current_data:
            current_item_date = spider.current_data.get(item['row']['document_id'])
            if current_item_date and item['row']['date'] > current_item_date:
                item['row']['updated'] = True
                if item['row']['relevant']:
                    spider.updated_items.append(item)
                    spider.updated += 1
            else:
                item['row']['updated'] = False

        return item
        #     raise DropItem('No update for {}'.format(item['row']['document_id']))


class DocumentDownloadPipeline(object):
    def process_item(self, item, spider):
        if item['row']['document_link'] == '':
            raise DropItem('No download for {}'.format(item['row']['document_id']))

        document = urllib2.urlopen(item['row']['document_link'])
        document_ext = item['row']['document_link'][item['row']['document_link'].rindex('.'):]

        output_file = os.path.join(item['row']['output_folder'], item['row']['file_number'] + document_ext)

        if not os.path.exists(item['row']['output_folder']):
            os.makedirs(item['row']['output_folder'])

        output = open(output_file, 'wb')
        output.write(document.read())
        output.close()
        return item



#todo: include list of relevant acs?
