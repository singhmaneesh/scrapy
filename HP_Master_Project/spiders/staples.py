# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import scrapy
import re
from scrapy import Request
from scrapy.log import WARNING
import urlparse

import urllib
from HP_Master_Project.utils import extract_first, clean_text, clean_list
from HP_Master_Project.items import ProductItem


class StaplesSpider(scrapy.Spider):
    name = 'staples_products'
    allowed_domains = ['staples.com', "www.staples.com"]

    SEARCH_URL = "http://www.staples.com/{search_term}/directory_{search_term}?sby=0&pn=0"

    PAGINATE_URL = "http://www.staples.com/{search_term}/directory_{search_term}?sby=0&pn={nao}"

    CURRENT_NAO = 1
    PAGINATE_BY = 18  # 18 products
    TOTAL_MATCHES = None  # for pagination

    PRICE_URL = 'http://www.staples.com/asgard-node/v1/nad/staplesus/price/{sku}?offer_flag=true' \
                '&warranty_flag=true' \
                '&coming_soon={metadata__coming_soon_flag}&' \
                'price_in_cart={metadata__price_in_cart_flag}' \
                '&productDocKey={prod_doc_key}' \
                '&product_type_id={metadata__product_type__id}&' \
                'preorder_flag={metadata__preorder_flag}' \
                '&street_date={street_date}' \
                '&channel_availability_for_id={metadata__channel_availability_for__id}' \
                '&backOrderFlag={metadata__backorder_flag}'
    HEADERS = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/56.0.2924.87 Safari/537.36"}

    def start_requests(self):
        yield Request(
            url=self.SEARCH_URL.format(search_term=urllib.quote_plus(self.searchterm.encode('utf-8'))),
            callback=self.parse_links, headers=self.HEADERS
        )

    def parse_links(self, response):
        totals = response.xpath('//input[contains(@id, "allProductsTabCount")]/@value').extract()
        if totals:
            totals = totals[0].replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)

        if self.TOTAL_MATCHES is None:
            self.log('No "next result page" link!')
            return
        if self.CURRENT_NAO * self.PAGINATE_BY >= self.TOTAL_MATCHES:
            return
        self.CURRENT_NAO += 1

        return Request(
            self.PAGINATE_URL.format(
                search_term=urllib.quote_plus(self.searchterm.encode('utf-8')),
                nao=str(self.CURRENT_NAO)),
            callback=self.parse,
            dont_filter=True
        )

    def parse(self, response):
        links = response.xpath('//a[contains(@property, "product-title")]/@href').extract()

        for link in links:
            link = urlparse.urljoin(response.url, link)
            yield Request(url=link, callback=self.parse_product, dont_filter=True, headers=self.HEADERS)

    def parse_product(self, response):
        product = ProductItem()

        if 'Good thing this is not permanent' in response.body_as_unicode():
            product['not_found'] = True
            return product

        maintenance_error = response.xpath('.//*[contains(text(), "The site is currently under maintenance.")]')
        if maintenance_error:
            self.log("Website under maintenance error, retrying request: {}".format(response.url), WARNING)
            return Request(response.url, callback=self.parse_product, meta=response.meta, dont_filter=True)

        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse image
        image = self._parse_image(response)
        product['image'] = image

        # Parse link
        product['link'] = response.url

        # Parse model
        model = self._parse_model(response)
        product['model'] = model

        # Parse upc
        upc = self._parse_upc(response)
        product['upc'] = upc

        # Parse ean
        product['ean'] = None

        # Parse currencycode
        product['currencycode'] = 'USD'

        # Set locale
        product['locale'] = 'en-US'

        # Parse price
        price = self._parse_price(response)
        product['price'] = price

        # Parse sale price
        product['saleprice'] = price

        # Parse sku
        sku = self._parse_sku(response)
        product['sku'] = sku

        # Parse retailer_key
        retailer_key = self._parse_retailer_key(response)
        product['retailer_key'] = retailer_key

        # Parse in_store
        in_store = self._parse_instore(response)
        product['instore'] = in_store

        # Parse ship to store
        ship_to_store = self._parse_shiptostore(response)
        product['shiptostore'] = ship_to_store

        # Parse shipping phrase
        shipping_phrase = self._parse_shippingphrase(response)
        product['shippingphrase'] = shipping_phrase

        # Parse stock status
        stock_status = self._parse_stock_status(response)
        product['productstockstatus'] = stock_status

        # Parse gallery
        product['gallery'] = None

        # Parse features

        features = self._parse_features(response)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        return product

    @staticmethod
    def _parse_name(response):
        title = extract_first(response.xpath('//span[contains(@itemprop, "name")]//text()').extract())
        return title

    @staticmethod
    def _parse_image(response):
        img = response.xpath('//img[contains(@class, "stp--sku-image")]/@src').extract()
        return img

    @staticmethod
    def _parse_sku(response):
        sku = extract_first(response.xpath('//span[contains(@itemprop, "sku")]/text()').extract())
        return sku

    @staticmethod
    def _parse_model(response):
        model = extract_first(response.xpath('//span[contains(@ng-bind, "product.metadata.mfpartnumber")]'
                                             '/text()').extract())
        return model




