BOT_NAME = "fdds_scrapper"

SPIDER_MODULES = ["fdds_scrapper.spiders"]
NEWSPIDER_MODULE = "fdds_scrapper.spiders"

ROBOTSTXT_OBEY = True

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
