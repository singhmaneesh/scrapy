# -*- coding: utf-8 -*-
import scrapy


class EnUsInsightSpider(scrapy.Spider):
    name = 'en-us_insight'
    allowed_domains = ['http://www.insight.com']
    start_urls = ['http://www.insight.com/']

    def parse(self, response):
        pass
