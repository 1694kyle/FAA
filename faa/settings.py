# -*- coding: utf-8 -*-

# Scrapy settings for faa project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'faa'

SPIDER_MODULES = ['faa.spiders']
NEWSPIDER_MODULE = 'faa.spiders'

AC_CSV = r'C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\advisory_circulars.csv'

AC_DOCUMENT_FOLDER = r'I:\FAA Guidance\Advisory Circulars'  # output parent folder
AC_DOCUMENT_FILE = r"C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\ac_data.csv"  # file to check dates

SPEC_DOCUMENT_FOLDER = r'I:\FAA Guidance\Specs'
SPEC_DOCUMENT_FILE = r"C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\spec_data.csv"

AC_HEADERS = 'document_id', 'date'
SPEC_HEADERS = ''

RELEVANT_AC_FILE = r"C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\relevant_offices"
RELEVANT_OFFICE_FILE = r'C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\relevant_offices'

RECIPIENT_FILE = r'C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\recipients'
EMAIL_TEMPLATE_AC_FILE = r'C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\email_template_ac'

ADDRESS_BOOK_FILE = r'C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\address_book.CSV'
# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en',
}

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# LOG_FILE = r'C:\Users\kbonnet\PycharmProjects\cwest\faa\faa\faa\files\crawling_log'
# open(LOG_FILE, 'wb').close()
# LOG_LEVEL = 'WARNING'
# LOG_STDOUT = True

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY=3
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP=16

# Disable cookies (enabled by default)
#COOKIES_ENABLED=False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED=False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'faa.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'faa.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'faa.pipelines.InitialPipeline': 100,
    'faa.pipelines.UpdatedPipeline': 200,
    'faa.pipelines.DocumentDownloadPipeline': 300,

}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
AUTOTHROTTLE_ENABLED=True
# The initial download delay
#AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG=False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS=0
#HTTPCACHE_DIR='httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES=[]
#HTTPCACHE_STORAGE='scrapy.extensions.httpcache.FilesystemCacheStorage'
