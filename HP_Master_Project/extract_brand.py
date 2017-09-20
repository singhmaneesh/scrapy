# ~~coding=utf-8~~

from pkg_resources import resource_string
import traceback
import csv

BRANDS = ()


def _load_brands(fname):
    """ Fills the global BRANDS variable """
    global BRANDS
    if BRANDS:  # don't perform expensive load operations
        return
    BRANDS = resource_string(__name__, fname)
    BRANDS = BRANDS.split('\n')
    BRANDS = [b.lower().strip().rstrip() for b in BRANDS]
    BRANDS = set(BRANDS)  # set lookup is faster than list lookup


def _brand_in_list(brand):
    """ Utility method to check if the given brand is in the list """
    global BRANDS
    return brand.lower() in BRANDS


def _find_brand(brand, fname='brand_data/brands.csv'):
    try:
        data = resource_string(__name__, fname)
        brandsreader = csv.reader(data.split('\n'), delimiter=',')
        for x in brandsreader:
            if brand in x:
                return x[0]
    except:
        print traceback.format_exc()


def extract_brand_from_first_words(text, fname='brand_data/brands.list', max_words=7):
    """ Tries to guess the brand in the given text, assuming that the
         given text starts with the brand name.
        Example: Apple Iphone 16GB
        Should normally return: Apple
    :param text: str containing brand
    :param max_words: int, longest brand possible
    :return: str or None
    """
    global BRANDS
    _load_brands(fname)
    # prepare the data
    if isinstance(text, str):
        text = text.decode('utf8')
    text = text.replace(u'®', ' ').replace(u'©', ' ').replace(u'™', ' ')
    text = text.strip().replace('  ', ' ')
    # take `max_words` first words; `max_words`-1; `max_words`-2; and so on
    for cur_words in list(reversed(range(max_words)))[0:-1]:
        partial_brand = text.split(' ')[0:cur_words]
        partial_brand = ' '.join(partial_brand)
        if _brand_in_list(partial_brand):
            return partial_brand
    # nothing has been found - try to get rid of 'the'
    if text.lower().startswith('the '):
        text = text[4:]
    for cur_words in list(reversed(range(max_words)))[0:-1]:
        partial_brand = text.split(' ')[0:cur_words]
        partial_brand = ' '.join(partial_brand)
        found_brand = _find_brand(partial_brand)
        if found_brand:
            return found_brand
        elif _brand_in_list(partial_brand):
            return partial_brand
