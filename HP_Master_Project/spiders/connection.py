# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import re
import urlparse
import math
import json

from HP_Master_Project.utils import extract_first, clean_text, clean_list
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider
from HP_Master_Project.extract_brand import extract_brand_from_first_words


class ConnectionSpider(BaseProductsSpider):
    name = "connection_products"
    allowed_domains = ['connection.com', 'www.connection.com']

    SEARCH_URL = 'https://www.connection.com/IPA/Shop/Product/Search?ManufId=4293851212+4293836821'

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    Paginate_URL = 'https://www.connection.com/product/searchpage?ManufId=4293851212+4293836821&Sort=Availability' \
                   '&pageNumber={page_num}&pageSize={result_per_page}&' \
                   'url=https://www.connection.com/IPA/Shop/Product/Search&mode=List'

    TOTAL_MATCHES = None

    RESULT_PER_PAGE = None

    def __init__(self, *args, **kwargs):
        super(ConnectionSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        self.retailer_check = False

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        product = ProductItem()

        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse brand
        brand = self._parse_brand(response)
        product['brand'] = brand

        # Parse image
        image = self._parse_image(response)
        product['image'] = image

        product['link'] = response.url

        # Parse model
        model = self._parse_model(response)
        product['model'] = model

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
        gallery = self._parse_gallery(response)
        product['gallery'] = gallery

        # Parse features

        features = self._parse_features(response)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        return product

    @staticmethod
    def _parse_name(response):
        name = extract_first(response.xpath('//h1[@class="pagetitle"]/text()'))
        return name

    def _parse_brand(self, response):
        brand = response.xpath('//span[@itemprop="brand"]/text()')
        if brand:
            return extract_first(brand)
        return 'HP'

    @staticmethod
    def _parse_image(response):
        image_url = extract_first(response.xpath('//a[@item-prop="image"]/@href'))
        return image_url

    @staticmethod
    def _parse_gallery(response):
        gallery = response.xpath('//div[contains(@id, "productImageBrowser")]'
                                 '//img[@class="img-responsive"]/@src').extract()
        return gallery

    def _parse_model(self, response):
        model = extract_first(response.xpath('//span[@itemprop="mpn"]/text()'))
        return clean_text(self, model)

    @staticmethod
    def _parse_price(response):
        price = extract_first(response.xpath('//span[@class="product-price"]'
                                             '/span[@class="priceDisplay"]/text()'))
        if price:
            return float(price.replace("$", "").replace(",", ""))

    def _parse_sku(self, response):
        sku = extract_first(response.xpath('//span[@itemprop="sku"]/text()'))
        return clean_text(self, sku)

    def _parse_retailer_key(self, response):
        retailer_key = extract_first(response.xpath('//span[@itemprop="sku"]/text()'))
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
    def _parse_stock_status(response):
        stock_value = 4
        stock_status = extract_first(response.xpath('//span[@id="productAvailability"]/text()'))
        stock_status = stock_status.lower()

        if stock_status == 'out of stock':
            stock_value = 0

        if stock_status == 'in stock':
            stock_value = 1

        if stock_status == 'call for availability':
            stock_value = 2

        if stock_status == 'discontinued':
            stock_value = 3

        return stock_value

    def _parse_features(self, response):
        features = []
        features_name = response.xpath('//ul[@id="productSpecsContainer"]'
                                       '/li//label[contains(@for, "product_spec")]/text()').extract()
        for f_name in features_name:
            f_content = response.xpath('//ul[@id="productSpecsContainer"]'
                                       '/li/div[contains(@id, "product_spec")]'
                                       '/*[@aria-label="%s"]'
                                       '//text()' % f_name).extract()
            f_content = clean_list(self, f_content)
            if len(f_content) > 1:
                f_content_title = response.xpath('//ul[@id="productSpecsContainer"]'
                                                 '/li/div[contains(@id, "product_spec")]'
                                                 '/*[@aria-label="%s"]'
                                                 '//span[@class="strong"]/text()' % f_name).extract()
                f_content_title = clean_list(self, f_content_title)

                f_content_text = response.xpath('//ul[@id="productSpecsContainer"]'
                                                '/li/div[contains(@id, "product_spec")]'
                                                '/*[@aria-label="%s"]'
                                                '//span[not(contains(@class,"strong"))]'
                                                '/text()' % f_name).extract()
                f_content_text = clean_list(self, f_content_text)

                for f_c_title in f_content_title:
                    index = f_content_title.index(f_c_title)
                    feature = {f_c_title.replace(":", ""): f_content_text[index]}
                    features.append(feature)

            else:
                f_content = f_content[0]
                f_content = clean_text(self, f_content)
                feature = {f_name: f_content}
                features.append(feature)

        return features

    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)
        totals = re.search('of (\d+) Results', response.body)
        if totals:
            totals = totals.group(1).replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)
                return int(totals)

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
        link_list = []
        if self.retailer_id:
            data = json.loads(response.body)
            for link in data:
                link = link['product_link']
                link_list.append(link)
            for link in link_list:
                url = urlparse.urljoin(response.url, link)
                yield url, ProductItem()
        else:
            links = response.xpath('//div[@class="product-name-list"]/a/@href').extract()
            for link in links:
                url = urlparse.urljoin(response.url, link)
                yield url, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None

        self.current_page += 1

        if (self.TOTAL_MATCHES and self.RESULT_PER_PAGE and
                    self.current_page < math.ceil(self.TOTAL_MATCHES / float(self.RESULT_PER_PAGE))):
            next_page = self.Paginate_URL.format(page_num=self.current_page,
                                                 result_per_page=self.RESULT_PER_PAGE)
            return next_page
