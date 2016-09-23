# -*- coding: utf-8 -*-

from scrapy import Item,Field

class ScrapytestItem(Item):
    city_id = Field()
    keyword_id = Field()
    url = Field()
    title = Field()
    content = Field()
    post_time = Field()
    source = Field()
    