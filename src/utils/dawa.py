import requests
import jmespath
from cachetools import LRUCache, cached

DAWA_BASE_URL = "https://api.dataforsyningen.dk"
cache = LRUCache(maxsize=4)


def get_postal_codes():
    res = requests.get(f"{DAWA_BASE_URL}/postnumre").json()
    postalcode_names = jmespath.search("[].navn", res)
    postal_codes = jmespath.search("[].nr", res)
    return postal_codes, postalcode_names


def get_city_names():
    res = requests.get(f"{DAWA_BASE_URL}/supplerendebynavne2").json()
    city_names = jmespath.search("[].navn", res)
    return city_names


def get_street_names():
    res = requests.get(f"{DAWA_BASE_URL}/vejnavne").json()
    street_names = jmespath.search("[].navn", res)
    return street_names


def get_region_names():
    res = requests.get(f"{DAWA_BASE_URL}/regioner").json()
    region_names = jmespath.search("[].navn", res)
    return region_names


@cached(cache=cache)
def get_address_data():
    postal_codes, postalcode_names = get_postal_codes()
    postalcode_names = list(set(postalcode_names))
    street_names = get_street_names()
    city_names = get_city_names()
    region_names = get_region_names()
    return region_names, city_names, postalcode_names, postal_codes, street_names