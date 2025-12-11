# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class OtodomScraperItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    price_per_m2 = scrapy.Field()
    location = scrapy.Field()
    area = scrapy.Field()
    rooms = scrapy.Field()
    heating = scrapy.Field()
    floor = scrapy.Field()
    rent = scrapy.Field()
    finish = scrapy.Field()
    market = scrapy.Field()
    ownership = scrapy.Field()
    available_from = scrapy.Field()
    advertiser_type = scrapy.Field()
    description = scrapy.Field()
    build_year = scrapy.Field()
    lift = scrapy.Field()
    building_type = scrapy.Field()
    windows = scrapy.Field()
    material = scrapy.Field()
    security = scrapy.Field()
    media = scrapy.Field()
    equipment = scrapy.Field()
    extras = scrapy.Field()
    url = scrapy.Field()

    #  Dodatkowe pola do przetwarzania
    floor_number = scrapy.Field()
    total_floors = scrapy.Field()
    street = scrapy.Field()
    neighbourhood = scrapy.Field()  # 
    district = scrapy.Field()
    city = scrapy.Field()
    region = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()