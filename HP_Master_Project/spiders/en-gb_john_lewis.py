# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import json
import re
import urlparse

import requests
from scrapy import Request

from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider, FormatterWithDefaults
from HP_Master_Project.utils import clean_text


class AgrosSpider(BaseProductsSpider):
    name = "en_gb_john_lewis"
    allowed_domains = ['www.johnlewis.com']
    # HOME_PAGE_URL = 'https://www.johnlewis.com/search?earch-term={search_term}'
    SEARCH_URL = 'https://www.johnlewis.com/search?incremental=true&page={page_num}&search-term={search_term}'

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
        page_title = response.css('body.standard-product-list-rest-page-body').extract_first()
        if page_title or self.retailer_id:
            return self.parse(response)

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

        # Parse categories
        categories = self._parse_categories(response)
        product['categories'] = categories

        # Parse sku
        sku = self._parse_sku(response)
        product['sku'] = sku

        # Parse retailer key
        retailer_key = self._parse_retailer_key(response)
        product['retailer_key'] = retailer_key
        
        # Parse retailer key 2
        retailer_key2 = self._parse_retailer_key2(response)
        product['ean'] = retailer_key2
        
        # Parse mpn
        mpn = self._parse_mpn(response)
        product['sku'] = mpn
        
        # Parse currencycode
        product['currencycode'] = self._parse_currency_code(response)

        # Set locale
        product['locale'] = 'en-gb'

        # Parse price
        price = self._parse_price(response)
        product['price'] = price

        # Parse ship to store
        ship_to_store = 1
        product['shiptostore'] = ship_to_store

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
        name = response.css('header.product-header h1::text').extract()
        if name:
            return name[0]

    @staticmethod
    def _parse_brand(response):
        brand = re.search('"brand":\s+"([^"]+)",', response.text)
        if brand:
            brand = brand.group(1)
            return brand

    @staticmethod
    def _parse_image(response):
        image_url = response.css('div.standard-product-column-left div.carousel img::attr(src)').extract_first()
        if image_url:
            image_url = ('http:' + image_url).split('?', 1)[0]
            return image_url

    @staticmethod
    def _parse_categories(response):
        categories = response.css('ul.breadcrumbs li a::text').extract()[1:]
        categories = [category.strip() for category in categories]
        return categories

    @staticmethod
    def _parse_sku(response):
        sku = re.search('Product code: (\d+)', response.text)
        if sku:
            sku = sku.group(1)
            return sku
    
    def _parse_retailer_key(self, response):
        retailer_key = response.css('div.add-to-wish-list-placeholder::attr(data-sku)').extract_first()
        if retailer_key:
            return retailer_key
    
    # def _parse_retailer_key2(self, response):
    #    retailer_key2 = response.url.rsplit('/', 1)[1].strip('p')
    #    if retailer_key2:
    #        return retailer_key2
    
    def _parse_mpn(self, response):
        mpn = response.xpath(
            '//dt[@class="product-specification-list__label" and contains(text(),"MPN")]/following::dd/text()').extract_first()
        if mpn:
            return mpn

    def _parse_gallery(self, response):
        if not self._parse_image(response):
            return None
        image_list = []
        image_urls = response.css('ul.product-images li img::attr(src)').extract()
        for image_url in image_urls:
            image_list.append('http:' + image_url.split('?', 1)[0])
        return image_list

    def _parse_model(self, response):
        model_number = response.xpath(
            '//dt[@class="product-specification-list__label" and contains(text(),"Model")]/following::dd/text()').extract_first()
        if model_number:
            return clean_text(self, model_number)

    @staticmethod
    def _parse_price(response):
        price = response.css('p.u-centred.price::text').extract_first()
        if price:
            price = float(price.replace(",", "").strip('\n').strip().strip('£'))
            return price

    @staticmethod
    def _parse_stock_status(response):
        stock_value = 4
        stock_status = response.css('div.add-to-basket-summary-and-cta button::text').extract_first()
        if stock_status:
            stock_status = stock_status.lower()

            if 'out of stock' in stock_status:
                stock_value = 0

            if 'add to basket' in stock_status:
                stock_value = 1
        return stock_value

    @staticmethod
    def _parse_currency_code(response):
        currency_code = re.search('"currencyCode":"([^"]+)"', response.body)
        if currency_code:
            currency_code = currency_code.group(1)
            return currency_code

    @staticmethod
    def _parse_features(response):
        feature_list = []
        features = response.xpath(
            '//dl[@class="product-specifications-list"]/dt[@class="product-specification-list__label"]/text()').extract()
        feature_values = response.xpath(
            '//dl[@class="product-specifications-list"]/dt[@class="product-specification-list__label"]/following::dd/text()').extract()
        for feature, value in zip(features, feature_values):
            feature_list.append({feature.strip(): value.strip()})
        return feature_list

    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        # total = len(response.css('section.product-list-item').extract())
        # if total and total.isdigit():
        #         if not self.TOTAL_MATCHES:
        #             self.TOTAL_MATCHES = int(total)
        #         return int(total)

    def _scrape_results_per_page(self, response):
        if self.retailer_id:
            return None
        result_per_page = len(response.css('section.product-list-item').extract())
        if result_per_page:
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
                product_request = Request(url=url, meta=meta, dont_filter=True)
                yield product_request, ProductItem()
        else:
            links = response.css('section.product-list-item a.product-list-link::attr(href)').extract()
            for link in links:
                url = urlparse.urljoin(response.url, link)
                yield url, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None

        self.current_page += 1
        if len(response.css('section.product-list-item').extract()) > 0:
            next_page = self.SEARCH_URL.format(page_num=self.current_page,
                                               search_term=response.meta['search_term'])
            return next_page
