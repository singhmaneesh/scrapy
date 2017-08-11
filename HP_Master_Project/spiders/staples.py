# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

from scrapy import Request
from scrapy.log import WARNING
import urlparse
import json
import json
import re
import time
import traceback

from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider


class StaplesSpider(BaseProductsSpider):
    name = 'staples_products'
    allowed_domains = ['staples.com', "www.staples.com"]

    SEARCH_URL = "http://www.staples.com/{search_term}/directory_{search_term}?sby=0&pn=0&akamai-feo=off"

    PAGINATE_URL = "http://www.staples.com/{search_term}/directory_{search_term}?sby=0&pn={nao}"

    LoadMore = "https://www.staples.com/search/loadMore"

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

    is_category = False

    def __init__(self, *args, **kwargs):
        self.is_category = False
        super(StaplesSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/56.0.2924.87 Safari/537.36")

    def start_requests(self):
        for request in super(StaplesSpider, self).start_requests():
            if not self.product_url:
                request = request.replace(callback=self.parse_search)
            yield request

    def parse_search(self, response):
        redirect = response.xpath('//div[@id="redirect"]')
        if redirect:
            category_url = re.findall("\.replace\('(.*?)'\)", response.body)
            if category_url:
                self.is_category = True
                url = urlparse.urljoin(response.url, category_url[0])
                return Request(url, meta=response.meta, callback=self.parse_category_links)
            else:
                return
        else:
            return self.parse(response)

    @staticmethod
    def parse_category_links(response):
        links = response.xpath('//div[contains(@class, "z_padding_")]'
                               '/a[contains(@class, "z_ctablue")]/@href').extract()
        for link in links:
            yield Request(url=link, meta=response.meta)

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        meta = response.meta.copy()
        product = meta.get('product', ProductItem())

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

        # Parse sale price
        # product['saleprice'] = price

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
        product['gallery'] = self._parse_gallery(response)

        # Parse features
        features = self._parse_features(response)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        # Parse price
        js_data = self.parse_js_data(response)
        try:
            if product.get("sku", ""):
                prod_doc_key = js_data['prod_doc_key']
                prod_doc_key = prod_doc_key.split("/")[:-1]
                prod_doc_key.append(product.get("sku", ""))
                prod_doc_key = "/".join(prod_doc_key)
            else:
                prod_doc_key = js_data['prod_doc_key']
            return Request(
                url=self.PRICE_URL.format(sku=sku,
                                          metadata__coming_soon_flag=js_data['metadata']['coming_soon_flag'],
                                          metadata__price_in_cart_flag=js_data['metadata']['price_in_cart_flag'],
                                          prod_doc_key=prod_doc_key,
                                          metadata__product_type__id=js_data['metadata']['product_type']['id'],
                                          metadata__preorder_flag=js_data['metadata']['preorder_flag'],
                                          street_date=time.time(),
                                          metadata__channel_availability_for__id=
                                          js_data['metadata']['channel_availability_for']['id'],
                                          metadata__backorder_flag=js_data['metadata']['backorder_flag']),
                dont_filter=True,
                callback=self._parse_price,
                meta=meta,
                headers={"Referer": None, "X-Requested-With": "XMLHttpRequest",
                         'User-Agent': 'Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)'}
            )
        except Exception as e:
            self.log("Error while forming request for base product data: {}".format(traceback.format_exc()), WARNING)
            return product

    @staticmethod
    def _parse_name(response):
        title = response.xpath('//span[contains(@itemprop, "name")]//text()').extract()
        if title:
            return title[0]

    @staticmethod
    def _parse_image(response):
        img = response.xpath('//img[contains(@class, "stp--sku-image")]/@src').extract()
        if img:
            return img[0]

    def _parse_sku(self, response):
        sku = response.xpath('//span[contains(@itemprop, "sku")]/text()').extract()
        if sku:
            return self.clear_text(sku[0])

    def _parse_model(self, response):
        model = response.xpath('//span[contains(@ng-bind, "product.metadata.mfpartnumber")]/text()').extract()
        if model:
            return self.clear_text(model[0])

    @staticmethod
    def _parse_upc(response):
        return None

    def _parse_price(self, response):
        meta = response.meta.copy()
        product = response.meta['product']
        try:
            jsonresponse = json.loads(response.body_as_unicode())
            if u'currentlyOutOfStock' in jsonresponse['cartAction']:
                product['productstockstatus'] = True
            else:
                product['productstockstatus'] = False

            product['price'] = jsonresponse['pricing']['finalPrice']
            return product

        except BaseException as e:
            self.log("Error parsing base product data: {}".format(e), WARNING)
            if 'No JSON object could be decoded' in e:
                self.log("Repeating base product data request: {}".format(e), WARNING)
                return Request(response.url, callback=self._parse_price, meta=meta, dont_filter=True)

    @staticmethod
    def _parse_retailer_key(response):
        return None

    @staticmethod
    def _parse_instore(response):
        return None

    @staticmethod
    def _parse_shiptostore(response):
        return None

    @staticmethod
    def _parse_stock_status(response):
        return None

    @staticmethod
    def _parse_shippingphrase(response):
        return None

    @staticmethod
    def _parse_features(response):
        return None

    def clear_text(self, str_result):
        return str_result.replace("\t", "").replace("\n", "").replace("\r", "").replace(u'\xa0', ' ').strip()

    def parse_js_data(self, response):
        data = response.xpath('.//script[contains(text(), "products[")]/text()').extract()
        data = data[0] if data else None
        if data:
            try:
                data = re.findall(r'\s?products\[[\"\'](.+)[\"\']\]\s?=\s?(.+);', data)
                js_data = json.loads(data[0][1])
                return js_data
            except BaseException:
                return

    def _scrape_total_matches(self, response):
        totals = response.xpath('//input[contains(@id, "allProductsTabCount")]/@value').extract()
        if totals:
            totals = totals[0].replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)
                return int(totals)

    def _scrape_product_links(self, response):
        links = response.xpath('//a[contains(@property, "url")]/@href').extract()

        if not links:
            links = response.xpath('.//div[@class="product-info"]'
                                   '/a[contains(@class, "product-title")]/@href').extract()
        if not links:
            links = response.xpath('//a[@class="product-title scTrack pfm"]/@href').extract()

        links = [urlparse.urljoin(response.url, x) for x in links]

        for link in links:
            yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        meta = response.meta
        current_page = meta.get('current_page')
        if not current_page:
            current_page = 1
        if self.TOTAL_MATCHES is None:
            self.log("No next link")
            return
        if current_page * self.PAGINATE_BY >= self.TOTAL_MATCHES:
            return
        current_page += 1
        meta['current_page'] = current_page

        if not self.is_category:
            url = self.PAGINATE_URL.format(search_term=meta['search_term'],
                                           nao=str(current_page))
        else:
            split_url = response.url.split('?')
            next_link = split_url[0]
            if len(split_url) == 1:
                url = (next_link + "?pn=%d" % current_page)
            else:
                next_link += "?"
                for s in split_url[1].split('&'):
                    if "pn=" not in s:
                        next_link += s + "&"
                url = (next_link + "pn=%d" % current_page)

        if url:
            return Request(url=url, meta=meta, dont_filter=True)
