# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

from scrapy import Request, FormRequest
from scrapy.log import WARNING
import urlparse
import json
import re
import time
import traceback

from HP_Master_Project.utils import clean_text, clean_list
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider


class StaplesSpider(BaseProductsSpider):
    name = 'staples_products'
    allowed_domains = ['staples.com', "www.staples.com"]

    SEARCH_URL = "http://www.staples.com/{search_term}/directory_{search_term}?sby=0&pn=0&akamai-feo=off"

    PAGINATE_URL = "http://www.staples.com/{search_term}/directory_{search_term}?sby=0&pn={nao}"

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    LoadMore = 'https://www.staples.com/search/loadMore'

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
            if self.retailer_id:
                request = request.replace(callback=self.parse)
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

    def parse_category_links(self, response):
        links = response.xpath('//div[@id="z_wrapper"]//ul[@class="z_main_nav"]'
                               '/li/a/@href').extract()
        links = links[1:][:-1]
        for link in links:
            yield Request(url=link, meta=response.meta, callback=self.parse_single_links, dont_filter=True)

    @staticmethod
    def parse_single_links(response):
        links = response.xpath('//div[contains(@class, "z_category")]/a[@class="z_cta"]/@href').extract()
        for link in links:
            yield Request(url=link, meta=response.meta, dont_filter=True)

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

    @staticmethod
    def _parse_categories(response):
        categories = response.xpath('//li[contains(@typeof, "Breadcrumb")]/a/text()').extract()
        return categories

    def _parse_model(self, response):
        model = response.xpath('//span[contains(@ng-bind, "product.metadata.mfpartnumber")]/text()').extract()
        if model:
            return self.clear_text(model[0])

    def _parse_upc(self, response):
        try:
            js_data = self.parse_js_data(response)
            upc = js_data['metadata']['upc_code']
            upc = upc[-12:]
            if len(upc) < 12:
                count = 12-len(upc)
                upc = '0'*count + upc
            return upc
        except Exception as e:
            self.log("Error while forming request for base product data: {}".format(traceback.format_exc()), WARNING)
            return None

    @staticmethod
    def _parse_gallery(response):
        gallery = response.xpath('//div[@class="thumbs-wrapper"]/ul[@ng-hide="showThumbnails"]/li/img/@src').extract()
        return gallery

    def _parse_price(self, response):
        meta = response.meta.copy()
        product = response.meta['product']
        try:
            jsonresponse = json.loads(response.body_as_unicode())
            if u'currentlyOutOfStock' in jsonresponse['cartAction']:
                product['productstockstatus'] = 0
            else:
                product['productstockstatus'] = 1

            product['price'] = jsonresponse['pricing']['nowPrice']
            product['saleprice'] = jsonresponse['pricing']['finalPrice']
            return product

        except BaseException as e:
            self.log("Error parsing base product data: {}".format(e), WARNING)
            if 'No JSON object could be decoded' in e:
                self.log("Repeating base product data request: {}".format(e), WARNING)
                return Request(response.url, callback=self._parse_price, meta=meta, dont_filter=True)

    def _parse_retailer_key(self, response):
        retailer_key = response.xpath('//span[contains(@itemprop, "sku")]/text()').extract()
        if retailer_key:
            return self.clear_text(retailer_key[0])

    def _parse_instore(self, response):
        if self._parse_price(response):
            return 1

        return 0

    def _parse_manufacturer(self, response):
        try:
            js_data = self.parse_js_data(response)
            manufacturer = js_data['metadata']['mfname']
            return manufacturer
        except Exception as e:
            self.log("Error while forming request for base product data: {}".format(traceback.format_exc()), WARNING)
            return None

    def _parse_shiptostore(self, response):
        try:
            js_data = self.parse_js_data(response)
            shiptostore = js_data['metadata']['ship_to_store_flag']
            return shiptostore
        except Exception as e:
            self.log("Error while forming request for base product data: {}".format(traceback.format_exc()), WARNING)
            return None

    @staticmethod
    def _parse_shippingphrase(response):
        return None

    def _parse_features(self, response):
        try:
            feature_list = []
            js_data = self.parse_js_data(response)
            features = js_data['description']['bullets']
            for feat in features:
                feature = feat['value']
                if ':' in feature:
                    feature_title = feature.split(':')[0]
                    feature_content = clean_text(self, feature.split(':')[1])
                    feature = {feature_title: feature_content}
                    feature_list.append(feature)
                else:
                    break
            return feature_list
        except Exception as e:
            self.log("Error while forming request for base product data: {}".format(traceback.format_exc()), WARNING)
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
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        try:
            totals = response.xpath('//input[contains(@id, "allProductsTabCount")]/@value')[0].extract()
            if not int(totals):
                totals = response.xpath('//span[@class="count"]/text()')[0].re('(\d+)')[0]
            if not int(totals):
                totals = response.xpath('//span[@class="results-number"]/text()').re('(\d+)')[0]
            if totals:
                totals = totals.replace(',', '').replace('.', '').strip()
                if totals.isdigit():
                    if not self.TOTAL_MATCHES:
                        self.TOTAL_MATCHES = int(totals)
                    return int(totals)
        except:
            self.log("Found no total matches {}".format(traceback.format_exc()))
            return 0

    def _scrape_product_links(self, response):
        links = response.xpath('//a[contains(@property, "url")]/@href').extract()

        if not links:
            links = response.xpath('.//div[@class="product-info"]'
                                   '/a[contains(@class, "product-title")]/@href').extract()
        if not links:
            links = response.xpath('//a[@class="product-title scTrack pfm"]/@href').extract()

        if self.retailer_id:
            data = json.loads(response.body)
            link_list = data
            for link in link_list:
                link = link['product_link']
                links.append(link)

        links = [urlparse.urljoin(response.url, x) for x in links]

        for link in links:
            yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None
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
                                           nao=str(current_page), dont_filter=True)
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
