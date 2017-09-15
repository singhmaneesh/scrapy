from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from HP_Master_Project.items import ProductItem
from HP_Master_Project.item_loader import ProductItemLoader

class HPSpider(CrawlSpider):
    name="en-US_HP.com"
    allowed_domains = ['hp.com', 'www.hp.com', 'store.hp.com']
    start_urls = ['http://www8.hp.com/us/en/sitemap.html', 'http://store.hp.com/sitemap-us.xml']
   
    rules = (
        Rule(LinkExtractor(allow=r'hp\.com\/us\/en\/pdp\/'), callback='parse_product', follow=False),
        Rule(LinkExtractor(allow=r'^http:\/\/store\.hp\.com\/us\/en\/'), follow=True),
    )

    def start_requests(self):
        for url in self.start_urls:
            if 'sitemap-us.xml' in url:
                yield Request(url, callback=self.parse_sitemap)
            else:
                yield Request(url)

    def parse_sitemap(self, response):
        for url in response.xpath('//*[name()="loc"]/text()').extract():
            url = url.strip()
            if '/us/en/pdp/' in url:
                yield Request(url, callback=self.parse_product)
            else:
                yield Request(url)

    def _extract_features(self, response):
        features = {}
        for div in response.css('div#specs div.large-12'):
            key = div.css('div.desc h2::text').extract_first()
            val = div.css('p.specsDescription span::text').extract_first()
            if key != None and val != None:
                features[key.strip()] = val.strip()
        return features

    def parse_product(self, response):
        l = ProductItemLoader(item=ProductItem(), response=response)
        l.add_css('name', 'h1.prodTitle > span::text')
        l.add_value('brand', u'HP')
        l.add_css('image', 'img[itemprop="image"]::attr(src)')
        l.add_value('link', response.url)
        l.add_css('model', 'span[itemprop="sku"]::text')
        # l.add_css('upc', '')
        # l.add_css('ean', '')
        l.add_css('currencycode', 'meta[itemprop="priceCurrency"]::attr(content)')
        l.add_value('locale', 'en-US')
        l.add_css('price', 'div.pdpPrice span.price_strike::text, div.priceBlock > span[itemprop="price"]::text')
        l.add_css('saleprice', 'div.priceBlock > span[itemprop="price"]::text')
        l.add_css('sku', 'span[itemprop="sku"]::text')
        l.add_css('retailer_key', 'span[itemprop="sku"]::text')
        l.add_css('instore', 'link[itemprop="availability"]::attr(href)')
        # l.add_css('shiptostore', '')
        l.add_css('shippingphrase', 'div.estShipMessagePDP::text')
        l.add_css('productstockstatus', 'link[itemprop="availability"]::attr(href)')
        l.add_css('categories', 'input[var="category"]::attr(value)')
        l.add_css('gallery', 'img[itemprop="image"]::attr(src)')
        
        features = self._extract_features(response)
        l.add_value('features', [{key: features[key]} for key in features])
        l.add_css('condition', 'link[itemprop="itemCondition"]::attr(href)')
        l.add_css('publisher', 'HP.com')
        l.add_value('manufacturer', features.get('Manufacturer', None))
        l.add_value('mpn', features.get('Manufacturer Part Number', None))
        item = l.load_item()
        if 'saleprice' in item and item['saleprice'] == item['price']:
            item['saleprice'] = None

        return item
    