# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

from scrapy.log import WARNING
from scrapy import Request
import re
import json
import math

from HP_Master_Project.utils import is_empty
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider
from HP_Master_Project.extract_brand import extract_brand_from_first_words


class EnGbHpSpider(BaseProductsSpider):
    name = 'en_gb_hp'
    allowed_domains = ['store.hp.com', 'www.hp.com']

    # SEARCH_URL = "http://store.hp.com/UKStore/Merch/Search.aspx?q={search_term}"
    SEARCH_URL = "http://store.hp.com/UKStore/Merch/Product.aspx?id=Z2W73EA&opt=ABU&sel=NTB"
    # http://store.hp.com/UKStore/Merch/Search.aspx?q

    # PAGINATE_URL = "http://store.hp.com/us/en/Finder?storeId=10151&catalogId=10051&categoryId=" \
    #                "&searchTerm={search_term}&searchType=" \
    #                "&searchTermScope=&pageSize=12&isAjax=true&beginIndex={begin_index}" \
    #                "&subCatFacet=&orderBy=99&pagingOnly=true"

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    CATEGORY_URL = "http://store.hp.com/webapp/wcs/stores/servlet/HPBreadCrumbView?productId={product_id}" \
                   "&langId=-1&storeId=10151&catalogId=10051&urlLangId=-1&modelId={model_id}"

    TOTAL_MATCHES = None

    def __init__(self, *args, **kwargs):
        super(EnGbHpSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/60.0.3112.90 Safari/537.36"

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        print (response)
        print ("afafdaf")
        product = ProductItem()
        print (product)

        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse image
        image = self._parse_image(response)
        product['image'] = image

        # Parse model
        model = self._parse_model(response)
        product['model'] = model

        # Parse ean
        product['ean'] = None

        # Parse currencycode
        product['currencycode'] = 'USD'

        # Set locale
        product['locale'] = 'en-US'

        # Parse sku
        sku = self._parse_sku(response)
        product['sku'] = sku

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

        # Parse categories
        product_id = re.search("productIdValue='(.*)';", response.body)
        model_id = re.search("temp = (\d+)+", response.body)
        model_id = model_id.group(1) if model_id else None
        return product

        if not model_id:
            model_id = re.search('retrieveBreadCrumbDetails(.*?);', response.body)
            print model_id
            model_id = model_id.group(1).replace('(', '').replace(')', '') if model_id else None
            model_id = model_id.split(',')[-1] if model_id else None
            print model_id
        # print(product)

        if product_id and model_id:
            return Request(
                url=self.CATEGORY_URL.format(product_id=product_id.group(1),
                                             model_id=model_id),
                callback=self._parse_categories,
                dont_filter=True,
                meta={"product": product},
                headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                       'Chrome/60.0.3112.90 Safari/537.36'}
            )


        return product

    @staticmethod
    def _parse_name(response):
        title = response.xpath('//h1[@class="pb-product__name"]/text()').extract()
        print (title)
        if title:
            return title[0]

    @staticmethod
    def _parse_image(response):
        img = response.xpath('//img[@itemprop="image"]/@src').extract()
        if img:
            return img[0]

    def _parse_sku(self, response):
        sku = response.xpath('//div[@class="prodSku"]/span[@class="prodNum"]/text()').extract()
        if sku:
            return self.clear_text(sku[0])

    def _parse_stock_status(self, response):
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

        except BaseException as e:
            self.log("Error parsing stock status data: {}".format(e), WARNING)

        return stock_value

    @staticmethod
    def _parse_categories(response):
        product = response.meta['product']

        categories = response.xpath('//ul[contains(@class, "breadcrumbs")]/li/a/text()').extract()
        product['categories'] = categories
        return product

    def _parse_model(self, response):
        model = response.xpath('//span[contains(@id, "mfr_no_id")]/text()').extract()
        if model:
            return self.clear_text(model[0])

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
        retailer_key = response.xpath('//div[@class="prodSku"]/span[@class="prodNum"]/text()').extract()
        if retailer_key:
            return self.clear_text(retailer_key[0])

    def _parse_instore(self, response):
        if self._parse_price(response):
            return 1

        return 0

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
            features_value_content = features_value[index].xpath('.//p[@class="specsDescription"]'
                                                                 '/span/text()').extract()
            if features_value_content:
                features_value_content = features_value_content[0]
            else:
                features_value_content = is_empty(features_value[index].xpath('.//a/@href').extract())
            feature = {f_name: self.clear_text(features_value_content)} if features_value_content else {f_name: ""}
            features.append(feature)

        return features

    def clear_text(self, str_result):
        return str_result.replace("\t", "").replace("\n", "").replace("\r", "").replace(u'\xa0', ' ').strip()

    def _scrape_total_matches(self, response):
        print ("_scrape_total_matches")
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        totals = response.xpath('//div[@class="searchCount"]/span[@class="searchTotal"]'
                                '/text()').extract()
        self.TOTAL_MATCHES = 1
        return self.TOTAL_MATCHES
        if totals:
            totals = re.search("(\d+) results", totals[0])
            if totals:
                totals = totals.group(1).replace(',', '').replace('.', '').strip()
                if totals.isdigit():
                    if not self.TOTAL_MATCHES:
                        self.TOTAL_MATCHES = int(totals)
                    return int(totals)

    def _scrape_product_links(self, response):
        print ("_scrape_product_links")
        link_list = []
        if self.retailer_id:
            data = json.loads(response.body)
            for link in data:
                link = link['product_link']
                link_list.append(link)
            for link in link_list:
                yield link, ProductItem()
        else:
            print ("_scrape_product_links11111111111")
            # print (response)
            yield self.parse_product(response)
            # print (response.body)
            links = response.xpath('//div[@class="productWrapper"]'
                                   '//div[@class="productInfo2"]//a[@class="productHdr"]/@href').extract()

            links = [response.urljoin(x) for x in links]

            for link in links:
                yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        print ("_scrape_next_results_page_link")
        if self.retailer_id:
            return None

        search_term = response.meta['search_term']
        self.current_page += 1

        begin_index = self.current_page * 12
        return None

        if self.current_page < math.ceil(self.TOTAL_MATCHES / 12.0):
            next_page = self.PAGINATE_URL.format(search_term=search_term, begin_index=begin_index)
            return next_page
