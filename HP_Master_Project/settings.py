# -*- coding: utf-8 -*-
# Scrapy settings for HP_Master_Project project

import os

BOT_NAME = 'HP_Master_Project'

SPIDER_MODULES = ['HP_Master_Project.spiders']
NEWSPIDER_MODULE = 'HP_Master_Project.spiders'

ITEM_PIPLINES = {
    'HP_Master_Project.CSVPipeline': 300
}
DOWNLOADER_MIDDLEWARES = {
    'HP_Master_Project.middlewares.RandomUserAgentMiddleware': 543,
}
ROBOTSTXT_OBEY = False

SHUB_KEY = os.getenv('1e43437dbeef4754bc239df039613488')
# if you want to run it locally, replace '999999' by your Scrapy Cloud project ID below
SHUB_PROJ_ID = os.getenv('SHUB_JOBKEY', '224177').split('/')[0]


