from scrapy.spiders import SitemapSpider
from HP_Master_Project.items import ProductItem
from scrapy import Request


class CDWSpider(SitemapSpider):
    name = "cdw.com"
    site_url = 'https://www.cdw.com'
    uri = {

    'computers': '/shop/search/Computers/result.aspx?w =C&key=&ln=0&b=CPQ&pCurrent=199&pPage=1',
    'displays':'/shop/search/Monitors-Projectors/result.aspx?w=D&key=&ln=0&b=CPQ',
    'printers_supplies':'/shop/search/Printers-Scanners-Print-Supplies/result.aspx?w=P&key=&ln=0&b=CPQ',
    'services': '/shop/search/Services/result.aspx?w=G&key=&ln=0&b=CPQ'
    }

    def start_requests(self):
        for key in self.uri:
            yield Request(
                url=self.site_url + self.uri[key],
                callback=self.parse_computers
            )
    def parse_computers(self, response):
        products = response.css('div.search-result')
        for prod in products:
            product_link = prod.css('div.column-2 > h2 > a::attr(href)').extract_first()
            product_link = self.parse_product_link(product_link)
            yield Request(
                url=product_link,
                callback=self.parse_product
            )


    def parse_product(self, response):
        product = ProductItem()
        product['name'] = response.css('h1#primaryProductName span::text').extract_first()
        product['image'] = response.css('div.main-media  > div.main-image >img::attr(src)').extract_first()
        product['link'] = response.url
        product['currencycode'] = response.css('div#singleContainer span[itemprop="priceCurrency"]::attr(content)').extract_first()
        product['price'] = response.css('div#singleContainer span[itemprop="price"]::attr(content)').extract_first()
        availability = response.css('div#primaryProductAvailability span::text').extract()
        product['productstockstatus'] = self.get_product_stock_status(availability)
        product['instore'] = self.get_instore_status(availability)
        product['locale'] = 'en-US'

        sku = response.css('div#primaryProductPartNumbers span.part-number')
        product['sku'] = sku[0].css('span span::text').extract_first()
        retailer_key = sku[1].css('span::text').extract_first()
        retailer_key = retailer_key.split(':')
        product['retailer_key'] = retailer_key[1]
        specs = response.css('div.feature-list ul li')
        product['features'] = self.get_specifications(specs)

        return product

    def parse_product_link(self, product_link):
        link =  self.site_url+ product_link
        return link

    def get_product_stock_status(self, availability):
        if availability == 'In Stock':
            return 1
        elif availability == 'Call':
            return 2
        else :
            return 4

    def get_instore_status(self, availability):
        if availability == 'In Stock':
            return 1
        else:
            return 0
    def get_specifications(self, specification_body):
        specs = []
        for spec in specification_body:
            specs.append(spec.css('::text').extract_first())
        return specs

