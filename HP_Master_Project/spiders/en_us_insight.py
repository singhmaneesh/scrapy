# -*- coding: utf-8 -*-
import scrapy
import json
import urlparse
import urllib
import logging

from HP_Master_Project.items import ProductItem


class EnUsInsightSpider(scrapy.Spider):
    name = 'en-us_insight'
    allowed_domains = ['http://www.insight.com']
    products_api = 'http://www.insight.com/insightweb/getProduct'
    product_api = 'http://www.insight.com/insightweb/getProductInfo'
    flag = False

    def start_requests(self):
        payload = json.dumps(self.get_next_products_payload(page=1))
        return [scrapy.Request(url=self.products_api, method='POST', body=payload,
                               headers={'Content-Type': 'application/json'},
                               callback=self.parse_products_api)]

    def parse_products_api(self, response):
        self.logger.info("Start parsing products response")
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        except Exception as e:
            self.logger.error(e.message)
        else:
            if self.flag:
                num_products = json_response["shown"]
                for i in range(num_products):
                    payload = json.dumps(self.get_product_payload(json_response, i))
                    yield scrapy.Request(url=self.product_api, method='POST', body=payload, dont_filter=True,
                                         headers={'Content-Type': 'application/json'},
                                         callback=self.parse_product_response)
            self.flag = True
            current_page = self.get_current_page(json_response)
            payload = json.dumps(self.get_next_products_payload(page=current_page + 1))
            yield scrapy.Request(url=self.products_api, method='POST', body=payload, dont_filter=True,
                                 headers={'Content-Type': 'application/json'}, callback=self.parse_products_api)

    def parse_product_response(self, response):
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        except Exception as e:
            self.logger.error(e.message)
        else:
            return self.parse_product_item(json_response)

    def parse_product_item(self, json_response):
        product = ProductItem()
        product["name"] = json_response["webProduct"]["description"]
        product["link"] = self.get_product_url(json_response)
        product["image"] = json_response["webProduct"]["image"]["largeImage"]
        product["categories"] = json_response["webProduct"]["categoryLabel"]
        product["model"] = json_response["webProduct"]["modelName"]
        product["price"] = float(json_response["webProduct"]["prices"][0]["price"])
        product["saleprice"] = float(json_response["webProduct"]["prices"][0]["price"])
        product["currencycode"] = json_response["webProduct"]["prices"][0]["currency"]
        product["locale"] = json_response["webProduct"]["localeDefaults"]["id"]["locale"]
        product["manufacturer"] = json_response["webProduct"]["manufacturerName"]
        product["brand"] = json_response["webProduct"]["manufacturerName"]
        product["features"] = self.get_product_features(json_response)
        product["retailer_key"] = json_response["webProduct"]["manufacturerPartNumber"]
        product["sku"] = json_response["webProduct"]["materialId"]
        product["ean"] = json_response["webProduct"]["unspscCode"]
        product["unspsc"] = json_response["webProduct"]["unspscCode"]
        product["productstockstatus"] = self.get_availability(json_response)
        product["instore"] = 1
        product["condition"] = 1
        return product

    def get_availability(self, json_response):
        if not json_response["webProduct"]["availabilityInfos"][0]["stockAvailability"] and \
                        json_response["webProduct"]["availabilityInfos"][0]["availablityMessage"] \
                        == "availability.status.callforavailability":
            return 2
        else:
            return 0

    def get_product_features(self, json_response):
        features = []
        for specs in json_response["webProduct"]["extendedSpecsMap"]:
            for spec in range(len(json_response["webProduct"]["extendedSpecsMap"][specs]["details"])):
                features.append({json_response["webProduct"]["extendedSpecsMap"][specs]["details"][spec]["label"]:
                                 json_response["webProduct"]["extendedSpecsMap"][specs]["details"][spec]["value"]})
        return features

    def get_product_url(self, json_response):
        insight_part_id = json_response["webProduct"]["insightPartNumber"]
        mfr_name = json_response["webProduct"]["manufacturerName"]
        mfr_part_id = json_response["webProduct"]["manufacturerPartNumber"]
        product_name = json_response["webProduct"]["description"]
        return self.parse_product_url(insight_id=insight_part_id, mfr_id=mfr_part_id,
                                      mfr_name=mfr_name, product_name=product_name)

    @staticmethod
    def get_current_page(json_response):
        return json_response["currentPage"]

    @staticmethod
    def get_product_payload(json_response, i):
        mfr_part_id = json_response["nugsProducts"][i]["manufacturerPartNumber"]
        payload = {"defaultPlant": "10",
                   "loadAccessories": False,
                   "cartFlag": False,
                   "fromcs": False,
                   "loadRecommendedProducts": False,
                   "salesOrg": "2400",
                   "user": {},
                   "locale": "en_us",
                   "softwareContractIds": [],
                   "similarMaterialId": mfr_part_id,
                   "contractId": None}
        return payload

    @staticmethod
    def parse_product_url(insight_id, mfr_id, mfr_name, product_name):
        base_url = u'http://www.insight.com/en_US/buy/product/'
        if insight_id:
            path = insight_id + '/' + mfr_name + '/' + mfr_id
        else:
            path = mfr_id + '/' + mfr_name + '/' + mfr_id
        quoted_path = urllib.quote(path, '/%')
        quoted_url = urlparse.urljoin(base_url, quoted_path)
        product_path = product_name.replace(' ', '-')
        product_url = quoted_url + '/' + product_path + '/'
        return product_url

    @staticmethod
    def get_next_products_payload(page, search_keyword="HP"):
        page_num = current_page = page
        payload = {"category": None,
                   "field": ["A-MARA-MFRNR~0007081792"],
                   "searchText": [],
                   "priceRangeLow": "",
                   "priceRangeHigh": "",
                   "inStockFilterType": "BothInStockAndOutOfStock",
                   "onlyApprovedItems": None,
                   "onlyAgreementProducts": None,
                   "inventoryBlowOut": None,
                   "defaultPlant": 10,
                   "defaultSort": False,
                   "page": page_num,
                   "shown": 10,
                   "shownFlag": True,
                   "noCLP": False,
                   "pageNumber": page_num,
                   "pageSize": '0',
                   "nugsSortBySelect": "BestMatch",
                   "returnSearchUrl": "",
                   "businessUnit": 2,
                   "fireProductInfo": False,
                   "salesOrg": 2400,
                   "fieldList": [],
                   "imageURL": "http://imagesqa01.insight.com",
                   "useBreadcrumb": False,
                   "fromcs": False,
                   "locale": "en_us",
                   "nonLoggedInIpsContractId": None,
                   "groupId": None,
                   "setId": None,
                   "categoryId": None,
                   "controller": None,
                   "groupName": None,
                   "shared": None,
                   "returnSearchURL": u"/en_US/search.html?qtype=all&q={search_keyword}&pq=%7B%22pageSize%22%3A10%2C%22"
                                      "currentPage%{current_page}%3A1%2C%22shownFlag%22%3Atrue%2C%22priceRangeLower%22%3A0%2C%22"
                                      "priceRangeUpper%22%3A0%2C%22cmtStandards%22%3Atrue%2C%22categoryId%22%3Anull%2C%22setType%22%3Anull"
                                      "%2C%22setId%22%3Anull%2C%22shared%22%3Anull%2C%22groupId%22%3Anull%2C%22cmtCustomerNumber%22%3Anull"
                                      "%2C%22groupName%22%3Anull%2C%22fromLicense%22%3Atrue%2C%22licenseContractIds%22%3Anull%2C%22"
                                      "programIds%22%3Anull%2C%22controller%22%3Anull%2C%22fromcs%22%3Afalse%2C%22searchTerms%22%3A%7B%22"
                                      "{search_keyword}%2520INC%22%3A%7B%22field%22%3A%22field%22%2C%22value%22%3A%22A-MARA-MFRNR~0007081792"
                                      "%22%7D%7D%2C%22sortBy%22%3A%22BestMatch%22%7D".format(current_page=current_page,
                                                                                             search_keyword=search_keyword)
                   }
        return payload
