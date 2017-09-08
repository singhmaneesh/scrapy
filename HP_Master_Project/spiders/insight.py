# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import re
import urlparse
import json
import requests
from scrapy import Request

from HP_Master_Project.utils import extract_first, clean_text
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider


class InsightSpider(BaseProductsSpider):
    name = "insight_products"
    allowed_domains = ['insight.com', 'www.insight.com']

    # SEARCH_URL = 'https://www.insight.com/en_US/search.html?qtype=all&q={search_term}' \
    #              '&pq={"pageSize":10,"currentPage":{page_num},"shownFlag":true,' \
    #              '"priceRangeLower":0,"priceRangeUpper":0,' \
    #              '"cmtStandards":true,"categoryId":null,"setType":null,"setId":null,"shared":null,' \
    #              '"groupId":null,"cmtCustomerNumber":null,"groupName":null,"fromLicense":true,' \
    #              '"licenseContractIds":null,"programIds":null,"controller":null,"fromcs":false,' \
    #              '"searchTerms":{""{search_term}"":{"field":"searchTerm","value":"{search_term}"}}}'

    SEARCH_URL = 'https://www.insight.com/en_US/search.html?qtype=all&q={search_term}'

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    PRODUCT_API = 'https://www.insight.com/insightweb/getProductInfo'
    DATA = {
        'cartFlag': 'false',
        'contractId': '',
        'defaultPlant': '10',
        'fromcs': 'false',
        'loadAccessories': 'false',
        'loadRecommendedProducts': 'true',
        'locale': 'en_us',
        'salesOrg': '2400',
        'searchText': ['G6U79AA'],
        'similarMaterialId': 'G6U79AA',
        'softwareContractIds': [],
        'user': {}
    }

    HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/60.0.3112.90 Safari/537.36",
               "Content-Type": "application/json; charset=UTF-8"}

    TOTAL_MATCHES = None

    RESULT_PER_PAGE = None

    def __init__(self, *args, **kwargs):
        super(InsightSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        # self.url_formatter = FormatterWithDefaults(page_num=1)

    def start_requests(self):
        for request in super(InsightSpider, self).start_requests():
            if self.product_url:
                request = request.replace(callback=self.parse_api_check, headers=self.HEADERS)
            if self.retailer_id:
                request = request.replace(callback=self.parse_retailer, headers=self.HEADERS)
            yield request

    def parse_api_check(self, response):
        product = ProductItem()
        product['link'] = response.url
        yield Request(url=self.PRODUCT_API, method="POST", body=json.dumps(self.DATA),
                      callback=self._parse_single_product, meta={'product': product})

    def parse_retailer(self, response):
        data = json.loads(response.body)
        link_list = data
        for link in link_list:
            link = link['product_link']
            url = urlparse.urljoin(response.url, link)
            yield Request(url, callback=self.parse_api_check)

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        product = response.meta['product']

        try:
            product_json = json.loads(response.body)
            product_json = product_json['products'][0]
        except:
            return

        # Parse name
        name = self._parse_name(product_json)
        product['name'] = name

        # Parse brand
        brand = self._parse_brand(product_json)
        product['brand'] = brand

        # Parse image
        image = self._parse_image(product_json)
        product['image'] = image

        # Parse image
        categories = self._parse_category(product_json)
        product['categories'] = categories

        product['link'] = response.url

        # Parse manufacturer
        manufacturer = self._parse_manufacturer(product_json)
        product['manufacturer'] = manufacturer

        # Parse model
        model = self._parse_model(product_json)
        product['model'] = model

        # Parse currencycode
        product['currencycode'] = 'USD'

        # Set locale
        product['locale'] = 'en-US'

        product['mpn'] = product_json['webProduct']['manufacturerPartNumber']

        # Parse price
        price = self._parse_price(product_json)
        product['price'] = price

        # Parse sale price
        product['saleprice'] = price

        # Parse sku
        sku = self._parse_sku(product_json)
        product['sku'] = sku

        # Parse retailer_key
        retailer_key = self._parse_retailer_key(product_json)
        product['retailer_key'] = retailer_key

        # Parse unspec
        unspec = self._parse_unspec(product_json)
        product['unspec'] = unspec

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
        stock_status = self._parse_stock_status(product_json)
        product['productstockstatus'] = stock_status

        # Parse gallery
        gallery = self._parse_gallery(response)
        product['gallery'] = gallery

        # Parse features

        features = self._parse_features(product_json)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        return product

    @staticmethod
    def _parse_name(product_json):
        name = product_json['description']
        return name

    @staticmethod
    def _parse_brand(product_json):
        brand = product_json['manufacturerName']
        return brand

    @staticmethod
    def _parse_image(product_json):
        image_url = product_json['image']['largeImage']
        return image_url

    @staticmethod
    def _parse_gallery(response):
        gallery = response.xpath('//div[contains(@id, "productImageBrowser")]'
                                 '//img[@class="img-responsive"]/@src').extract()
        return gallery

    @staticmethod
    def _parse_unspec(product_json):
        unspec = product_json['unspscCode']
        return unspec

    @staticmethod
    def _parse_category(product_json):
        categories = product_json['webProduct']['categoryLabel']
        return categories

    @staticmethod
    def _parse_model(product_json):
        model = product_json['modelName']
        return model

    @staticmethod
    def _parse_manufacturer(product_json):
        manufacturer = product_json['manufacturerName']
        return manufacturer

    @staticmethod
    def _parse_price(product_json):
        price_list = product_json['prices']
        for single_price in price_list:
            if single_price['priceLabel'] == 'LISTPRICELABEL':
                price = single_price['price']
                return price

    @staticmethod
    def _parse_sku(product_json):
        sku = product_json['webProduct']['materialId']
        return sku

    def _parse_retailer_key(self, product_json):
        retailer_key = product_json['materialId']
        return clean_text(self, retailer_key)

    def _parse_instore(self, response):
        if self._parse_price(response):
            return 1

        return 0

    def _parse_shiptostore(self, response):
        if self._parse_shippingphrase(response):
            return 1

        return 0

    @staticmethod
    def _parse_shippingphrase(response):
        shipping_phrase = extract_first(response.xpath('//span[@id="productEstimatedShipping"]/text()'))
        return shipping_phrase

    @staticmethod
    def _parse_stock_status(product_json):
        stock_value = 4
        stock_status = product_json['availabilityInfos'][0]['availablityMessage']
        stock_status = stock_status.lower()

        discon_status = product_json['discontinuedStatus']

        if 'outofstock' in stock_status:
            stock_value = 0

        if 'instock' in stock_status:
            stock_value = 1

        if 'call for availability' in stock_status:
            stock_value = 2

        if discon_status:
            stock_value = 3

        return stock_value

    @staticmethod
    def _parse_features(product_json):
        features = []
        feature_content = product_json['webProduct']['extendedSpecsMap']
        for feat in feature_content:
            feature = {feat['details']['label']: feat['details']['value']}
            features.append(feature)

        return features

    def _scrape_total_matches(self, response):
        totals = re.search('of (\d+) Results', response.body)
        if totals:
            totals = totals.group(1).replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)
                return int(totals)
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

    def _scrape_results_per_page(self, response):
        if self.retailer_id:
            return None
        result_per_page = re.search('1 - (\d+) of', response.body)
        if result_per_page:
            result_per_page = result_per_page.group(1).replace(',', '').replace('.', '').strip()
            if result_per_page.isdigit():
                if not self.RESULT_PER_PAGE:
                    self.RESULT_PER_PAGE = int(result_per_page)
                return int(result_per_page)

    def _scrape_product_links(self, response):
        links = response.xpath('//div[@class="product-name-list"]/a/@href').extract()

        if not links:
            data = json.loads(response.body)
            link_list = data
            for link in link_list:
                link = link['product_link']
                links.append(link)

        for link in links:
            url = urlparse.urljoin(response.url, link)
            yield url, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None
        page_count = self.TOTAL_MATCHES / self.RESULT_PER_PAGE + 1

        self.current_page += 1

        if self.current_page <= page_count:
            next_page = self.SEARCH_URL.format(page_num=self.current_page,
                                               search_term=response.meta['search_term'])
            return next_page
