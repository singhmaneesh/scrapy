# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import re
import urlparse
import json
from pyvirtualdisplay import Display
from selenium import webdriver

from HP_Master_Project.utils import clean_text
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider


class InsightSpider(BaseProductsSpider):
    name = "insight_products"
    allowed_domains = ['insight.com', 'www.insight.com']

    SEARCH_URL = 'https://www.insight.com/en_US/search.html?qtype=all&q={search_term}'

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    TOTAL_MATCHES = None

    RESULT_PER_PAGE = None

    def __init__(self, *args, **kwargs):
        super(InsightSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        self.timeout = 90
        self.width = 1024
        self.height = 768

    def start_requests(self):
        for request in super(InsightSpider, self).start_requests():
            yield request

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def _prepare_driver(self, driver):
        driver.set_page_load_timeout(int(self.timeout))
        driver.set_script_timeout(int(self.timeout))
        driver.set_window_size(int(self.width), int(self.height))
        return driver

    def parse_product(self, response):
        product = response.meta['product']

        display = Display(visible=False)
        display.start()
        driver = webdriver.Firefox()
        self._prepare_driver(driver)

        driver.get(response.url)

        # Parse name
        name = self._parse_name(driver)
        product['name'] = name

        # Parse brand
        brand = self._parse_brand(driver)
        product['brand'] = brand

        # Parse image
        image = self._parse_image(driver)
        product['image'] = image

        # Parse image
        categories = self._parse_category(driver)
        product['categories'] = categories

        product['link'] = response.url

        # Parse manufacturer
        manufacturer = self._parse_manufacturer(driver)
        product['manufacturer'] = manufacturer

        # Parse model
        model = self._parse_model(driver)
        product['model'] = model

        # Parse currencycode
        product['currencycode'] = 'USD'

        # Set locale
        product['locale'] = 'en-US'

        product['mpn'] = driver.find_element_by_xpath("//div[@itemprop='mpn']").text
        # Parse price

        price = self._parse_price(driver)
        product['price'] = price

        product['saleprice'] = price

        # Parse sku
        sku = self._parse_sku(driver)
        product['sku'] = sku

        # Parse retailer_key
        retailer_key = self._parse_retailer_key(driver)
        product['retailer_key'] = retailer_key

        # Parse unspec
        unspec = self._parse_unspec(driver)
        product['unspec'] = unspec

        # Parse in_store
        in_store = self._parse_instore(response)
        product['instore'] = in_store

        # Parse stock status

        stock_info = self._parse_stock_status(driver)
        product['productstockstatus'] = stock_info

        # Parse gallery
        gallery = self._parse_gallery(driver)
        product['gallery'] = gallery

        # # Parse features

        features = self._parse_features(driver)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        return product

    @staticmethod
    def _parse_name(driver):
        name = driver.find_element_by_xpath('//div[@id="js-product-detail-target"]/h1/a').text
        return name

    @staticmethod
    def _parse_brand(driver):
        brand = driver.find_element_by_xpath('//div[@itemprop="brand"]').text
        return brand

    @staticmethod
    def _parse_image(driver):
        image_url = driver.find_element_by_xpath('//img[@itemprop="image"]').get_property("src")
        return image_url

    @staticmethod
    def _parse_gallery(driver):
        gallery_list = []
        gallerys = driver.find_elements_by_xpath('//li[contains(@class, "ccs-ds-zoomGallery-thumbs-inactive")]/img')
        for gallery in gallerys:
            gallery_list.append(gallery.get_property("src"))
        return gallery_list

    @staticmethod
    def _parse_unspec(driver):
        unspec_list = driver.find_elements_by_xpath('//div[contains(@class, "prod-description")]'
                                                    '//table[contains(@class, "product-specs")]//td')
        for unspec in unspec_list:
            if 'UNSPSC' in unspec.text:
                unspec = re.search('UNSPSC: (\d+)', unspec.text).group(1)
                return unspec

    @staticmethod
    def _parse_category(driver):
        category_list = []
        categories = driver.find_elements_by_xpath('//div[contains(@id, "breadcrumb")]'
                                                   '//li[@itemprop="itemListElement"]'
                                                   '//span[@itemprop="name"]')
        for category in categories:
            category_list.append(category.text)
        return category_list

    @staticmethod
    def _parse_model(driver):
        model = driver.find_element_by_xpath('//div[@itemprop="model"]').text
        return model

    @staticmethod
    def _parse_manufacturer(driver):
        manufacturer_list = driver.find_elements_by_xpath('//div[contains(@class, "prod-description")]'
                                                          '//table[contains(@class, "product-specs")]//td')
        for manufacturer in manufacturer_list:
            if 'Mfr' in manufacturer.text:
                manufacturer = re.search('Mfr. # (.*)', manufacturer.text).group(1)
                return manufacturer

    @staticmethod
    def _parse_price(driver):
        price_list = driver.find_elements_by_xpath('//p[@class="prod-price"]')
        for single_price in price_list:
            if single_price.text:
                price = re.search('USD (.*)', single_price.text).group(1)
                price = float(price.replace(',', '').replace('$', ''))
                return price

    @staticmethod
    def _parse_sku(driver):
        sku_list = driver.find_elements_by_xpath('//div[contains(@class, "prod-description")]'
                                                 '//table[contains(@class, "product-specs")]//td')
        for sku in sku_list:
            if 'Mfr' in sku.text:
                sku = re.search('Mfr. # (.*)', sku.text).group(1)
                return sku

    def _parse_retailer_key(self, driver):
        retailer_key_list = driver.find_elements_by_xpath('//div[contains(@class, "prod-description")]'
                                                          '//table[contains(@class, "product-specs")]//td')
        for retailer_key in retailer_key_list:
            if 'Mfr' in retailer_key.text:
                retailer_key = re.search('Mfr. # (.*)', retailer_key.text).group(1)
                return clean_text(self, retailer_key)

    def _parse_instore(self, driver):
        if self._parse_price(driver):
            return 1

        return 0

    @staticmethod
    def _parse_stock_status(driver):
        stock_value = 4
        stock_status = driver.find_element_by_xpath('//p[@class="prod-stock"]').text
        if 'in stock' in stock_status.lower():
            stock_value = 1
        if 'out of stock' in stock_status.lower():
            stock_value = 0
        if 'call for availability' in stock_status.lower():
            stock_value = 2
        if 'discontinued' in stock_status.lower():
            stock_value = 3
        return stock_value

    @staticmethod
    def _parse_features(driver):
        features = []
        features_name = driver.find_elements_by_xpath('//div[contains(@id, "specification-")]'
                                                      '/div//tr/td[@scope="row"]')
        features_value = driver.find_elements_by_xpath('//div[contains(@id, "specification-")]'
                                                       '/div//tr/td[not(contains(@scope,"row"))]')

        for f_name in features_name:
            index = features_name.index(f_name)
            feature = {f_name.text: features_value[index].text}
            features.append(feature)

        return features

    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        display = Display(visible=False)
        display.start()
        driver1 = webdriver.Firefox()
        self._prepare_driver(driver1)

        driver1.get(response.url)

        totals = driver1.find_element_by_xpath('//a[@data-label="Products"]').get_property("data-count")
        if totals:
            totals = totals.replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)
                return int(totals)

    def _scrape_results_per_page(self, response):
        if self.retailer_id:
            return None
        display = Display(visible=False)
        display.start()
        driver2 = webdriver.Firefox()
        self._prepare_driver(driver2)

        driver2.get(response.url)

        result_per_page = driver2.find_element_by_xpath("//a[@id='buy-search-pagesize-button']")\
            .get_property("data-selected")
        if result_per_page:
            result_per_page = result_per_page.group.replace(',', '').replace('.', '').strip()
            if result_per_page.isdigit():
                if not self.RESULT_PER_PAGE:
                    self.RESULT_PER_PAGE = int(result_per_page)
                return int(result_per_page)

    def _scrape_product_links(self, response):
        link_list = []
        if self.retailer_id:
            data = json.loads(response.body)
            links = data
            for link in links:
                link = link['product_link']
                link_list.append(link)
        else:
            display = Display(visible=False)
            display.start()
            driver3 = webdriver.Firefox()
            self._prepare_driver(driver3)

            driver3.get(response.url)
            links = driver3.find_elements_by_xpath('//div[@id="js-search-product-items"]'
                                                  '/div[@itemprop="itemListElement"]/a[@class="select-prod"]')
            if links:
                for link in links:
                    link = link.get_property("href")
                    link_list.append(link)

        for link in link_list:
            url = urlparse.urljoin(response.url, link)
            yield url, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None
        display = Display(visible=False)
        display.start()
        driver4 = webdriver.Firefox()
        self._prepare_driver(driver4)

        driver4.get(response.url)

        next_page = driver4.find_element_by_xpath('//div[@class="stickyPagination"]/a').click()
        return next_page
