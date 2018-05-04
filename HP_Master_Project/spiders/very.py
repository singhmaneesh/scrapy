# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

from scrapy.log import WARNING
from scrapy import Request
import re
import json
import math
import requests
import time

from HP_Master_Project.utils import is_empty
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider, FormatterWithDefaults
from HP_Master_Project.extract_brand import extract_brand_from_first_words


class VerySpider(BaseProductsSpider):
    name = "en-GB_Very.co.uk"
    allowed_domains = ['very.co.uk', 'www.very.co.uk']

    SEARCH_URL = "https://www.very.co.uk/e/q/{search_term}.end"

    API_URL = \
        'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    TOTAL_MATCHES = None

    def __init__(self, *args, **kwargs):
        super(VerySpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/60.0.3112.90 Safari/537.36"
        #self.url_formatter = FormatterWithDefaults(page_num=1)

    def start_requests(self):
        print "Start Requests Called"
        for request in super(VerySpider, self).start_requests():
            if not self.product_url:
                request = request.replace(callback=self.parse_search, dont_filter=True)
            yield request

    def parse_search(self, response):
        print "Parse Search Called"
        page_title = response.xpath('//ul[@class="productList"]').extract()
        if page_title or self.retailer_id:
            return self.parse(response)
        else:
            return self._parse_single_product(response)

    def _parse_single_product(self, response):
        print "Parse Single Product Called"
        return self.parse_product(response)

    def parse_product(self, response):
        print "Parse Product Called"
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
        product['mpn'] = model

        ean = self._parse_ean(response)
        product['ean'] = ean

        # Parse categories
        categories = self._parse_categories(response)
        product['categories'] = categories

        # Parse unspec DOUBT DOUBT
        #unspec = self._parse_unspec(response)
        #product['unspec'] = unspec

        # Parse currencycode
        product['currencycode'] = 'GBP'

        # Set locale
        product['locale'] = 'en-UK'

        # Parse price
        price = self._parse_price(response)
        product['price'] = price

        # Parse price
        sku = self._parse_sku(response)
        product['sku'] = sku

        # Parse retailer_key
        retailer_key = self._parse_retailer_key(response)
        product['retailer_key'] = retailer_key

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

    def _parse_name(self, response):
        name = response.xpath("//h1[@class='productHeading']//text()").extract()
        if name:
            name = ''.join(name)
            name = ' '.join(name.split())
            return name

    def _parse_brand(self, response):
        brand = response.xpath("//h1[@class='productHeading']//text()").extract()
        return brand[0].encode('utf-8').strip()

        if brand:
            return brand

    def _parse_sku(self, response):
        sku = response.xpath("/html/head/script[3]/text()").extract()[0].encode('utf8').replace('\n','').strip()
        skuData = re.search("(?<=sku: \")(.*)(?=\",url)",sku)
        if skuData:
            return skuData.group(0)

    def _parse_stock_status(self, response):
        stock_status = response.xpath("//meta[@property='product:availability']/@content").extract()
        if stock_status:
            return stock_status[0]

    def _parse_retailer_key(self, response):
        retailer_key = response.xpath("//span[@id='catalogueNumber']/text()").extract()
        if retailer_key:
            return retailer_key[0]

    def _parse_image(self, response):
        image = response.xpath("//li[@class='productImageItem']/a/@href").extract()
        if image:
            return image[0]

    def _parse_model(self, response):
        model = response.xpath("//span[@id='productMPN']/text()").extract()[-1].strip()
        if model:
            return model

    def _parse_ean(self, response):
        ean = response.xpath("//span[@id='productEAN']/text()").extract()[-1].strip()
        if ean:
            return ean

    def _parse_categories(self, response):
        categories = response.xpath("//li[@itemprop='itemListElement']//text()").extract()
        if categories:
            categories = filter(lambda a: a != '\n', categories)
            categories = filter(lambda a: a != '/', categories)
            categories.remove(u'Home')
            #model = '|'.join(model)
            return categories

    def _parse_price(self, response):
        price = response.xpath("//div[@class='priceNow']//text()").extract()
        price = ''.join(price)
        price = price.replace('Now','').strip()
        if price:
            x = price.encode('utf8')
            x = x[2:]
            return x

    def _parse_gallery(self, response):
        gallery = response.xpath("//li[@class='productImageItem']/a/@href").extract()
        return gallery

    def _parse_features(self, response):
        features = []
        features_name = response.xpath("//div[@id='productSpecification']/table//tr/td[1]/text()").extract()
        features_value = response.xpath("//div[@id='productSpecification']/table//tr/td[2]")

        for f_name in features_name:
            index = features_name.index(f_name)
            features_value_content = features_value[index].xpath('text()').extract()[0]
            if features_value_content:
                features_value_content = features_value_content
            feature = {f_name: features_value_content} if features_value_content else {f_name: ""}
            features.append(feature)
        return features
        

    def _scrape_total_matches(self, response):
        print "Scrape Total Matches Called"
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        totals = response.xpath("//div[@class='productsPerPage']/span/text()").extract()[0].encode('utf8')
        totals = totals.strip()
        if totals:
            totals = re.search("[0-9]+[)]", str(totals))
            if totals:
                totals = totals.group(0).replace(')','').replace(',', '').replace('.', '').strip()
                if totals.isdigit():
                    if not self.TOTAL_MATCHES:
                        self.TOTAL_MATCHES = int(totals)

                    return int(totals)

    def _scrape_product_links(self, response):
        print "Scrape Product Links Called"
        link_list = []
        if self.retailer_id:
            data = requests.get(self.API_URL.format(retailer_id=self.retailer_id)).json()
            for link in data:
                link = link['product_link']
                link_list.append(link)
            for link in link_list:
                url = link
                yield (url, ProductItem())
        else:
            links = response.xpath("//a[@class='productMainImage']/@href").extract()
            for link in links:
                yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        print "Scrape Next Results Page Called"
        if self.retailer_id:
            return None
        #search_term = response.meta['search_term']
        self.current_page += 1
        if self.current_page==2:
            self.SEARCH_URL = response.url
            print "FIRST PAGE: ---------- ", self.SEARCH_URL
        #else:
        #    self.SEARCH_URL = self.SEARCH_URL.split('?pageNumber=')[0]
        if self.current_page < math.ceil(self.TOTAL_MATCHES / 12.0):
            next_page = self.SEARCH_URL + "?pageNumber=" + str(self.current_page)
            return next_page