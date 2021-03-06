# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


from scrapy import signals
from scrapy.contrib.exporter import CsvItemExporter


class HpMasterProjectPipeline(object):
    def process_item(self, item, spider):
        return item


class CSVPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)

    def spider_opened(self, spider):
        if spider.name == 'connection_products':
            result_connection = open('crawler connection.csv', 'w+b')
            self.files[spider] = result_connection
            self.exporter = CsvItemExporter(result_connection)
            self.exporter.fields_to_export = ['name', 'brand', 'image', 'link', 'model', 'upc', 'ean', 'currencycode',
                                              'locale', 'price', 'saleprice', 'sku', 'retailer_key', 'instore',
                                              'shiptostore', 'shippingphrase', 'productstockstatus', 'categories',
                                              'gallery', 'features', 'condition']

        if spider.name == 'staples_products':
            result_staples = open('crawler staples.csv', 'w+b')
            self.files[spider] = result_staples
            self.exporter = CsvItemExporter(result_staples)
            self.exporter.fields_to_export = ['name', 'brand', 'image', 'link', 'model', 'upc', 'ean', 'currencycode',
                                              'locale', 'price', 'saleprice', 'sku', 'retailer_key', 'instore',
                                              'shiptostore', 'shippingphrase', 'productstockstatus', 'categories',
                                              'gallery', 'features', 'condition']

        if spider.name == 'zones_products':
            result_zones = open('crawler zones.csv', 'w+b')
            self.files[spider] = result_zones
            self.exporter = CsvItemExporter(result_zones)
            self.exporter.fields_to_export = ['name', 'brand', 'image', 'link', 'model', 'upc', 'ean', 'currencycode',
                                              'locale', 'price', 'saleprice', 'sku', 'retailer_key', 'instore',
                                              'shiptostore', 'shippingphrase', 'productstockstatus', 'categories',
                                              'gallery', 'features', 'condition']

        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        result_file = self.files.pop(spider)
        result_file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item