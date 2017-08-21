# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

from scrapy import Request, FormRequest
from scrapy.log import WARNING
import re
import urlparse

from HP_Master_Project.utils import is_empty
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider


class HpSpider(BaseProductsSpider):
    name = 'hp_products'
    allowed_domains = ['store.hp.com', "www.hp.com"]

    SEARCH_URL = "http://store.hp.com/us/en/SearchDisplay?client=&searchTerm={search_term}&search=&charset=utf-8" \
                 "&storeId=10151&catalogId=10051&langId=-1&beginIndex=0&pageSize=12"

    HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/60.0.3112.90 Safari/537.36"}

    def __init__(self, *args, **kwargs):
        self.is_category = False
        super(HpSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)

    def start_requests(self):
        for request in super(HpSpider, self).start_requests():
            if not self.product_url:
                request = request.replace(dont_filter=True, headers=self.HEADERS)
            yield request

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        product = response.meta['product']

        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse image
        image = self._parse_image(response)
        product['image'] = image

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

        # Parse sku
        sku = self._parse_sku(response)
        product['sku'] = sku

        # Parse manufacturer
        manufacturer = self._parse_manufacturer(response)
        product['manufacturer'] = manufacturer

        # Parse categories
        categories = self._parse_categories(response)
        product['categories'] = categories

        # Parse price
        price = self._parse_price(response)
        product['price'] = price

        # Parse sale price
        product['saleprice'] = price

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

        # Parse gallery
        product['gallery'] = self._parse_gallery(response)

        # Parse features
        features = self._parse_features(response)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        # Parse productstockstatus
        product['productstockstatus'] = self._parse_stock_status(response)

        return product

    @staticmethod
    def _parse_name(response):
        title = response.xpath('//span[@itemprop="name"]/text()').extract()
        if title:
            return title[0]

    @staticmethod
    def _parse_image(response):
        img = response.xpath('//img[@itemprop="image"]/@src').extract()
        if img:
            return img[0]

    def _parse_sku(self, response):
        sku = response.xpath('//span[@id="item_no_id"]/text()').extract()
        if sku:
            return self.clear_text(sku[0])

    def _parse_stock_status(self, response):
        product = response.meta['product']
        stock_value = 4

        try:
            stock_message = response.xpath('//*[@itemprop="availability"]/@href')[0].extract()

            if 'instock' in stock_message.lower():
                stock_value = 1
            if 'outofstock' in stock_message.lower():
                stock_value = 0
            if 'callforavailability' in stock_message.lower():
                stock_value = 2
            if 'discontinued' in stock_message.lower():
                stock_value = 3

            product['productstockstatus'] = stock_value
            return product

        except BaseException as e:
            self.log("Error parsing stock status data: {}".format(e), WARNING)
            product['productstockstatus'] = stock_value
            return product

    @staticmethod
    def _parse_categories(response):
        categories = response.xpath('//ul[contains(@class, "breadcrumbs")]/li/a/text()').extract()
        return categories

    def _parse_model(self, response):
        model = response.xpath('//span[contains(@id, "mfr_no_id")]/text()').extract()
        if model:
            return self.clear_text(model[0])

    def _parse_upc(self, response):
        return

    @staticmethod
    def _parse_gallery(response):
        gallery = response.xpath('//ul[@id="featured_image_pager"]/li/a/img/@src').extract()
        return gallery

    @staticmethod
    def _parse_price(response):
        price = response.xpath('//span[@itemprop="price"]/text()').extract()
        if price:
            return float(price[0].replace("$", "").replace(",", ""))

    def _parse_retailer_key(self, response):
        retailer_key = response.xpath('//span[@id="item_no_id"]/text()').extract()
        if retailer_key:
            return self.clear_text(retailer_key[0])

    def _parse_instore(self, response):
        if self._parse_price(response):
            return 1

        return 0

    def _parse_manufacturer(self, response):
        manufacture = re.search('name="mfgrname" value="(.*?)"', response.body)
        if manufacture:
            return self.clear_text(manufacture.group(1))

    def _parse_shiptostore(self, response):
        if self._parse_shippingphrase(response):
            return 1

        return 0

    def _parse_shippingphrase(self, response):
        pharse = response.xpath('//div[@class="estShipMessagePDP"]/text()').extract()
        if pharse:
            return self.clear_text(pharse[0])

    def _parse_features(self, response):
        features = []
        features_name = response.xpath('//div[contains(@class, "large-12")]/div[contains(@class, "large-5")]'
                                       '/div[contains(@class, "desc")]/h2/text()').extract()
        features_value = response.xpath('//div[contains(@class, "large-12")]/div[contains(@class, "large-7")]')

        for f_name in features_name:
            index = features_name.index(f_name)
            features_value_content = is_empty(features_value[index].xpath('.//p[@class="specsDescription"]'
                                                                          '/span/text()').extract())
            if features_value_content:
                features_value_content = features_value_content[0]
            else:
                features_value_content = is_empty(features_value[index].xpath('.//a/@href').extract())
            feature = {f_name: self.clear_text(features_value_content)}
            features.append(feature)

        return features

    def clear_text(self, str_result):
        return str_result.replace("\t", "").replace("\n", "").replace("\r", "").replace(u'\xa0', ' ').strip()

    def _scrape_total_matches(self, response):
        totals = response.xpath('//div[@class="searchCount"]/span[@class="searchTotal"]'
                                '/text()').extract()
        if totals:
            totals = re.search("(\d+) results", totals[0])
            if totals:
                totals = totals.group(1).replace(',', '').replace('.', '').strip()
                if totals.isdigit():
                    return int(totals)

    def _scrape_product_links(self, response):
        links = response.xpath('//div[contains(@id, "searchResults")]//div[@class="productWrapper"]'
                               '//div[@class="productInfo2"]//a[@class="productHdr"]/@href').extract()

        for link in links:
            link = urlparse.urljoin(response.url, link)
            yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        return None
