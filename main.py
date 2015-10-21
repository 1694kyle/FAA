from scrapy.crawler import CrawlerProcess
from faa.spiders.ac_spider import AcSpider
from faa.spiders.ac_spider_pandas import AcSpiderPandas


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())

process.crawl(AcSpiderPandas)
process.start()
