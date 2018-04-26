# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import re
import urlparse
import json
import requests
import string
import math

from scrapy import Request
from HP_Master_Project.utils import extract_first, clean_text, clean_list
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider, FormatterWithDefaults
from HP_Master_Project.extract_brand import extract_brand_from_first_words


class AgrosSpider(BaseProductsSpider):
    name = "en_gb_agros"
    allowed_domains = ['www.argos.co.uk', 'agros.co.uk']

    SEARCH_URL = 'http://www.argos.co.uk/search/hp/{search_term}/opt/page:{page_num}/'

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    TOTAL_MATCHES = None

    RESULT_PER_PAGE = None

    def __init__(self, *args, **kwargs):
        super(AgrosSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        self.user_agent = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/60.0.3112.90 Safari/537.36")
        self.url_formatter = FormatterWithDefaults(page_num=1)

    def start_requests(self):
        for request in super(AgrosSpider, self).start_requests():
            if not self.product_url:
                request = request.replace(callback=self.parse_search, dont_filter=True)
            yield request

    def parse_search(self, response):
        page_title = response.css('div.search-results-count').extract()
        if page_title or self.retailer_id:
            return self.parse(response)

        else:
            pass
            # category_url = response.xpath('//div[@class="button-lockup -center"]/a/@href').extract()
            # for c_url in category_url:
            #     link = urlparse.urljoin(response.url, c_url)
            #     return Request(url=link, meta=response.meta, callback=self.parse_category_link, dont_filter=True)

    # def parse_category_link(self, response):
    #     links = response.xpath('//div[contains(@class, "button-lockup")]'
    #                            '/a/@href').extract()
    #     if links:
    #         for link in links:
    #             href = urlparse.urljoin(response.url, link)
    #             yield Request(url=href, meta=response.meta, dont_filter=True, callback=self.parse_category_links)

    # @staticmethod
    # def parse_category_links(response):
    #     link = response.xpath('//div[contains(@class, "multi-button")]/div[@class="dropdown"]'
    #                           '/a/@href').extract()
    #     for l in link:
    #         if 'shop' in l:
    #             l = urlparse.urljoin(response.url, l)
    #             yield Request(url=l, meta=response.meta, dont_filter=True)

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

        product['ean'] = self._parse_ean(response)

        # Parse categories
        categories = self._parse_categories(response)
        product['categories'] = categories
        
        sku = self._parse_sku(response)
        product['sku'] = sku

        # Parse unspec
        # unspec = self._parse_unspec(response)
        # product['unspec'] = unspec

        # Parse currencycode
        product['currencycode'] = self._parse_currency_code(response)

        # Set locale
        product['locale'] = 'en-US'

        # Parse price
        price = self._parse_price(response)
        product['price'] = price

        # Parse sale price
        product['saleprice'] = price

        # Parse in_store
        in_store = self._parse_instore(response)
        product['instore'] = in_store

        # Parse ship to store
        ship_to_store = self._parse_shiptostore(response)
        product['shiptostore'] = ship_to_store

        # Parse shipping phrase
        # shipping_phrase = self._parse_shippingphrase(response)
        # product['shippingphrase'] = shipping_phrase

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
    def _parse_ean(response):
        ean = re.search('EAN: ([^<]+)</li>', response.text)
        if ean:
            ean = ean.group(1).strip().strip('.')
            return ean

    @staticmethod
    def _parse_name(response):
        name = response.css('h1.product-name-main span[itemprop="name"]::text').extract()
        if name:
            return name[0]

    @staticmethod
    def _parse_brand(response):
        brand = response.css('a[itemprop="brand"]::text').extract()
        # if not brand:
        #     brand = response.xpath('//span[@class="brand"]/text()').extract()
        return brand[0].strip() if brand else None

    @staticmethod
    def _parse_image(response):
        image_url = response.css('ul.media-player-items li.active img::attr(src)').extract()
        if image_url:
            image_url = ('http:' + image_url[0]).split('?', 1)[0]
            return image_url

    @staticmethod
    def _parse_categories(response):
        categories = response.css('li.breadcrumb__item span[itemprop="name"]::text').extract()
        return categories
    
    @staticmethod
    def _parse_sku(response):
        sku = response.url.rsplit('/', 1)[1]
        return sku

    # @staticmethod
    # def _parse_unspec(response):
    #     unspec = response.xpath('//span[@itemprop="gtin8"]/text()').extract()
    #     if unspec:
    #         return unspec[0]

    def _parse_gallery(self, response):
        if not self._parse_image(response):
            return None
        image_list = []
        image_urls = response.css('ul.media-player-thumbnails-list li button img::attr(src)').extract()
        for image_url in image_urls:
            image_list.append('http:' + image_url.split('?', 1)[0])
        return image_list

    def _parse_model(self, response):
        # TODO
        model = re.search('Model number:([^<]+)</p>', response.text)
        if model:
            model = model.group(1).strip()
            return clean_text(self, model)

    @staticmethod
    def _parse_price(response):
        price = response.css('li[itemprop="price"]::attr(content)').extract()
        if price:
            return float((price[0].replace(",", "")))

    def _parse_instore(self, response):
        # TODO
        # if self._parse_price(response):
        #     return 1

        return 0

    def _parse_shiptostore(self, response):
        # TODO
        # if self._parse_shippingphrase(response):
        #     return 1

        return 0

    @staticmethod
    def _parse_shippingphrase(response):
        # shipping_phrase = response.xpath('//div[@class="long-message-block"]//text()').extract()
        # return "".join(shipping_phrase).strip()
        pass

    def _parse_stock_status(self, response):
        stock_value = 4
        # stock_status = response.xpath('//link[@itemprop="availability"]/@href').extract()
        # if stock_status:
        #     stock_status = stock_status[0].lower()
        #
        # if 'outofstock' in stock_status:
        #     stock_value = 0
        #
        # if 'instock' in stock_status:
        #     stock_value = 1
        #
        # if self._parse_shippingphrase(response) == 'Call for availability':
        #     stock_value = 2
        #
        # if 'discontinued' in stock_status:
        #     stock_value = 3

        return stock_value

    def _parse_features(self, response):
        features = response.css('div.product-description-content-text li::text').extract()
        return features

    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        totals = re.search('Showing 1 - \d+ of (\d+) products</div>', response.body)
        if totals:
            totals = totals.group(1).replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)
                return int(totals)

    def _scrape_results_per_page(self, response):
        if self.retailer_id:
            return None
        result_per_page = re.search('Showing 1 - (\d+) of \d+ products</div>', response.body)
        if result_per_page:
            result_per_page = result_per_page.group(1).replace(',', '').replace('.', '').strip()
            if result_per_page.isdigit():
                if not self.RESULT_PER_PAGE:
                    self.RESULT_PER_PAGE = int(result_per_page)
                return int(result_per_page)

    def _scrape_product_links(self, response):
        link_list = []
        if self.retailer_id:
            data = requests.get(self.API_URL.format(retailer_id=self.retailer_id)).json()
            for link in data:
                link = link['product_link']
                link_list.append(link)
            for link in link_list:
                url = urlparse.urljoin(response.url, link)
                meta = response.meta
                meta['fire'] = True
                meta['dont_redirect'] = True
                # stopping 301 redirects
                product_request = Request(url=link, meta=meta, dont_filter=True)
                yield url, ProductItem()
        else:
            links = response.css('div.product-list a.ac-product-link::attr(href)').extract()
            for link in links:
                url = urlparse.urljoin(response.url, link)
                yield url, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None

        self.current_page += 1

        if (self.TOTAL_MATCHES and self.RESULT_PER_PAGE and
                self.current_page < math.ceil(self.TOTAL_MATCHES / float(self.RESULT_PER_PAGE))):
            next_page = self.SEARCH_URL.format(page_num=self.current_page,
                                               search_term=response.meta['search_term'])
            return next_page

    @staticmethod
    def _parse_currency_code(response):
        currency_code = response.css('span[itemprop="priceCurrency"]::attr(content)').extract()
        if currency_code:
            return currency_code[0]
