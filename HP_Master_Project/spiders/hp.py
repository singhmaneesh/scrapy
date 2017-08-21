from scrapy.spiders import SitemapSpider
from HP_Master_Project.items import ProductItem
from HP_Master_Project.item_loader import ProductItemLoader

class HPSpider(SitemapSpider):
    name="en-US_HP.com"
    sitemap_urls = ['http://store.hp.com/sitemap-us.xml']
    sitemap_rules = [
        ('/us/en/pdp/', 'parse_product'),
    ]

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
        if item['saleprice'] == item['price']:
            item['saleprice'] = None

        return item
    