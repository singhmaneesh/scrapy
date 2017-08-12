from scrapy.spiders import SitemapSpider
from HP_Master_Project.items import ProductItem
from HP_Master_Project.item_loader import ProductItemLoader

class HPSpider(SitemapSpider):
    name="hp.com"
    sitemap_urls = ['http://store.hp.com/sitemap-us.xml']
    sitemap_rules = [
        ('/us/en/pdp/', 'parse_product'),
    ]

    def parse_product(self, response):
        l = ProductItemLoader(item=ProductItem(), response=response)
        l.add_css('name', 'h1.prodTitle > span::text')
        l.add_css('brand', 'div[itemprop="brand"]::text')
        l.add_css('image', 'img[itemprop="image"]::attr(src)')
        l.add_value('link', response.url)
        # l.add_css('model', '')
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
        # l.add_css('shippingphrase', '')
        l.add_css('productstockstatus', 'link[itemprop="availability"]::attr(href)')
        l.add_css('categories', 'section.heroProducts  ul.breadcrumbs2 > li:nth-child(n+2):nth-last-child(n+2) > a::text')
        l.add_css('gallery', 'img[itemprop="image"]::attr(src)')
        l.add_css('features', '#features h2::text, #features p::text')
        l.add_css('condition', 'link[itemprop="itemCondition"]::attr(href)')
        # l.add_css('publisher', '')
        # l.add_css('manufacturer', '')
        item = l.load_item()
        if item['saleprice'] == item['price']:
            item['saleprice'] = None

        return item
    