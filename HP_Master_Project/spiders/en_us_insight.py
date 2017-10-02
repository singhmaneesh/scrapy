# -*- coding: utf-8 -*-
import scrapy
import json
import urlparse
import urllib
import re

from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider


class EnUsInsightSpider(BaseProductsSpider):
    name = 'en-us_insight'
    allowed_domains = ['insight.com']
    products_api = 'https://www.insight.com/insightweb/getProduct'
    product_api = 'https://www.insight.com/insightweb/getProductInfo'
    flag = False

    SEARCH_URL = 'https://www.insight.com/en_US/search.html?qtype=all&q={search_term}'

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'


    def __init__(self, *args, **kwargs):
        self.current_page=0
        super(EnUsInsightSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)


    def start_requests(self):
        for request in super(EnUsInsightSpider, self).start_requests():
            if not self.product_url:
                request = request.replace(callback=self.parse_search)
            if self.retailer_id:
                request = request.replace(callback=self.parse)
            yield request


    def parse_search(self, response):
        payload = json.dumps(self.get_next_products_payload(page=1))
        self.current_page+=1
        return [scrapy.Request(url=self.products_api, method='POST', body=payload,
                               headers={'Content-Type': 'application/json'}, meta=response.meta)]


    def _scrape_results_per_page(self, response):
        result_per_page = None
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        else:
            try:
                result_per_page = int(json_response["shown"])
            except Exception as e:
                self.logger.error(e.message)
        return result_per_page


    def _scrape_product_links(self, response):
        self.logger.info("Start parsing products response")
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        except Exception as e:
            self.logger.error(e.message)
        else:
            try:
                num_products = int(json_response["shown"])
            except:
                if json_response:
                    for item in json_response:
                        mfr_part_id = self.get_mfr_part_num_from_url(item["product_link"])
                        payload = json.dumps(self.get_product_payload(json_response, mfr_part_id))
                        meta = response.meta
                        meta['fire'] = True
                        product_request = scrapy.Request(url=self.product_api, method='POST', body=payload, meta=meta,
                                                         headers={'Content-Type': 'application/json'},
                                                         callback = self.parse, dont_filter = True)
                        yield product_request, ProductItem()
            else:
                for i in range(num_products):
                    mfr_part_id = json_response["nugsProducts"][i]["manufacturerPartNumber"]
                    payload = json.dumps(self.get_product_payload(json_response, mfr_part_id))
                    meta = response.meta
                    meta['fire'] = True
                    product_request = scrapy.Request(url=self.product_api, method='POST', body=payload, dont_filter=True,
                                                     headers={'Content-Type': 'application/json'},
                                                     meta=meta, callback=self.parse, )
                    yield product_request, ProductItem()


    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)
        total_matches = None
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        except Exception as e:
            self.logger.error(e.message)
        else:
            try:
                total_matches = int(json_response["nugsHitCount"])
            except:
                return None
        return total_matches


    def _scrape_next_results_page_link(self, response):
        next_page_request = None
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        except Exception as e:
            self.logger.error(e.message)
        else:
            current_page = self.get_current_page(self, json_response)
            if current_page:
                payload = json.dumps(self.get_next_products_payload(page=current_page+1))
                next_page_request = scrapy.Request(url=self.products_api, method='POST', body=payload, dont_filter=True,
                                               headers={'Content-Type': 'application/json'}, meta=response.meta)
            else:
                payload = json.dumps(self.get_next_products_payload(page=1))
                next_page_request = scrapy.Request(url=self.products_api, method='POST', body=payload, dont_filter=True,
                                                   headers={'Content-Type': 'application/json'}, meta=response.meta)
        return next_page_request


    def _parse_single_product(self, response):
        return self.parse_product(response)


    def parse_product(self, response):
        meta = response.meta.copy()
        product = meta.get('product', ProductItem())
        try:
            json_response = json.loads(response.body.decode("utf-8", "ignore"))
        except TypeError as e:
            self.logger.error(e.message + "Json respone cannot be parsed")
        except Exception as e:
            self.logger.error(e.message)
        else:
            return self.parse_product_item(json_response, product)


    def parse_product_item(self, json_response, product):
        if json_response.get("webProduct"):
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
            product["retailer_key"] = json_response["webProduct"]["materialId"]
            product["sku"] = json_response["webProduct"]["materialId"]
            product["ean"] = json_response["webProduct"]["unspscCode"]
            product["unspsc"] = json_response["webProduct"]["unspscCode"]
            product["productstockstatus"] = self.get_availability(json_response)
            product["instore"] = 1
            product["condition"] = 1
            return product
        else:
            return None

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

    def get_mfr_part_num_from_url(self, url):
        mfr_part_id = re.findall(r'/[a-zA-Z0-9%]+/', url)[1].replace('/','').replace('%23','#')
        return mfr_part_id


    @staticmethod
    def get_current_page(self, json_response):
        current_page = None
        try:
            current_page = json_response["currentPage"]
        except Exception as e:
            self.logger.error(e.message)
        return current_page


    @staticmethod
    def get_product_payload(json_response, mfr_part_id):
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
