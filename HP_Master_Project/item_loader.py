# -*- coding: utf-8 -*-
from scrapy.loader.processors import Compose, MapCompose, Join, TakeFirst
from scrapy.loader import ItemLoader
from HP_Master_Project.items import ProductItem
import re

__all__ = ['ProductItemLoader']

clean_text = Compose(MapCompose(lambda v: v.strip()), Join(';'))   
# features_out  = Compose(MapCompose(lambda v: v.strip()), Join('\n'))
price_out  = Compose(MapCompose(lambda v: re.sub(r'[^\d\.]', '', v)), TakeFirst(), float)
to_int = Compose(TakeFirst(), int)

def condition_out(field, values):
    if len(values) > 0:
        v = values[0]
        if 'New' in v:
            return 1
        elif 'Refurbished' in v:
            return 2
        elif 'Used' in v:
            return 3
        elif 'Damaged' in v:
            return 4
    else:
        return 0

def productstockstatus_out(field, values):
    if len(values) > 0:
        v = values[0].lower()
        if 'outofstock' in v:
            return 0
        elif 'instock' in v:
            return 1
        elif 'call for availability' in v:
            return 2
        elif 'discontinued' in v:
            return 3
    return 4

def instore_out(field, values):
    if len(values) > 0:
        v = values[0].lower()
        if 'instock' in v:
            return 1
    return None

class ProductItemLoader(ItemLoader):
    default_item_class = ProductItem
    name_in = MapCompose(unicode.strip)
    name_out = TakeFirst()
    brand_in = MapCompose(unicode.strip)
    brand_out = TakeFirst()
    image_in = MapCompose(unicode.strip)
    image_out = TakeFirst()
    link_out = TakeFirst()
    model_in = MapCompose(unicode.strip)
    model_out = TakeFirst()
    upc_out = to_int
    ean_out = to_int
    currencycode_out = TakeFirst()
    locale_out = TakeFirst()
    price_out = price_out
    saleprice_out = price_out
    sku_out = TakeFirst()
    retailer_key_in = MapCompose(unicode.strip)
    retailer_key_out = TakeFirst()
    instore_out = instore_out
    shiptostore_out = TakeFirst()
    shippingphrase_in = MapCompose(unicode.strip)
    shippingphrase_out = TakeFirst()
    productstockstatus_out = productstockstatus_out     # Integer (outOfStock=0, inStock=1, call for availability=2, Discontinued=3,Other=4)
    categories_in = MapCompose(unicode.strip)
    gallery_in = MapCompose(unicode.strip)
    # features_out = features_out
    condition_out = condition_out
    publisher_in = MapCompose(unicode.strip)
    publisher_out = TakeFirst()
    manufacturer_in = MapCompose(unicode.strip)
    manufacturer_out = TakeFirst()