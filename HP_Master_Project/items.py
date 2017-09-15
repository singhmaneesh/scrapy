# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ProductItem(scrapy.Item):
    # define the fields for your item here like:
    site = scrapy.Field()
    search_term = scrapy.Field()
    ranking = scrapy.Field()
    total_matches = scrapy.Field()
    results_per_page = scrapy.Field()
    scraped_results_per_page = scrapy.Field()
    is_single_result = scrapy.Field()

    name = scrapy.Field()   # String
    brand = scrapy.Field()  # String
    image = scrapy.Field()  # String
    link = scrapy.Field()   # String
    model = scrapy.Field()  # String, Alphanumeric code
    upc = scrapy.Field()    # Integer, 12 digit code
    ean = scrapy.Field()    # Integer, 13 digit International Article Number
    unspsc = scrapy.Field()
    currencycode = scrapy.Field()   # String
    locale = scrapy.Field()     # String
    unspec = scrapy.Field()
    price = scrapy.Field()  # Float
    saleprice = scrapy.Field()  # Float
    sku = scrapy.Field()    # String
    retailer_key = scrapy.Field()   # String
    instore = scrapy.Field()    # Integer (available for purchase in-store: 1, unavailable: 0)
    shiptostore = scrapy.Field()    # Integer
    shippingphrase = scrapy.Field()     # String
    productstockstatus = scrapy.Field()     # Integer (outOfStock=0, inStock=1, call for availability=2, Discontinued=3,Other=4)
    categories = scrapy.Field()     # String
    gallery = scrapy.Field()    # String
    features = scrapy.Field()   # String
    condition = scrapy.Field()  # Integer (New=1, Refurbished=2, Used=3, Damaged=4)
    publisher = scrapy.Field()  # String
    manufacturer = scrapy.Field()   # String
    mpn = scrapy.Field() # String - Manufacturer Part Number



