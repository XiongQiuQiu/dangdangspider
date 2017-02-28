import  scrapy
import requests
from scrapy import selector
from ..items import DangdangItem
from scrapy_redis.spiders import RedisSpider

class DangdangSpider(RedisSpider):
    name = 'dangdangspider'
    redis_key = 'dangdangspider:urls'
    allowed_domains = ['dangdang.com']
    start_urls = 'http://category.dangdang.com/cp01.00.00.00.00.00.html'

    def start_requests(self):
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
        headers = {'User-Agent': user_agent}
        yield scrapy.Request(url=self.start_urls, headers=headers, method='GET', callback=self.parse)

    def parse(self, response):
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
        headers = {'User-Agent': user_agent}
        lists = response.body.decode('gbk')
        bookslist = lists.xpath('//*[@id="leftCate"]/ul/li')
        for booklist in bookslist:
            try:
                category_big_name = booklist.xpath('a/text()').extract().pop().replace(' ', '')
                category_big_id = booklist.xpath('a/@href').extract().pop().split('.')[1]
                category_big_url = 'http://category.dangdang.com/cp01.{}.00.00.00.00.htm'.format(str(category_big_id))
                yield scrapy.Request(url=category_big_url, headers=headers, callback=self.detail_parse, meta={"ID1":category_big_id,"ID1_name":category_big_name})
            except Exception:
                pass

    def detail_parse(self, response):
        '''

        :param response:
        :return:
        '''
        url = 'http://category.dangdang.com/pg1-cp01.{}.00.00.00.00.html'.format(response.meta["ID1"])
        category_small = response.body.decode('gbk')
        booklists = category_small.xpaht('//*[@class="sort_box"]/ul/li[1]/div/span')
        for booklist in booklists:
            try:
                category_small_name = booklist.xpath('a//text()').extract().pop().replcae(' ', '').split('(')[0]
                category_small_id = booklist.xpath('a//text()').extract().pop().replace(' ', '').split('(')[0]
                category_small_url = "http://category.dangdang.com/pg1-cp01.{}.{}.00.00.00.html".\
                                  format(str(response.meta["ID1"]),str(category_small_id))
                yield scrapy.Request(url=category_small_url, callback=self.three_parse,
                                     meta={"ID1": response.meta["ID1"],
                                           "ID1_name": response.meta["ID1_name"], "ID2": category_small_id,
                                           "ID2_name": category_small_name})
            except Exception:
                pass

    def three_parse(self, response):
        for i in range(1, 101):
            url = 'http://category.dangdang.com/pg{}-cp01.{}.{}.00.00.00.html'.format(str(i),response.meta["ID1"],\
                                                                                      response.meta["ID3"])
            try:
                booklist = response.xpath('//*[@class="list_aa listimg"]/li')
                for book in booklist:
                    item = DangdangItem()
                    try:
                        item['title'] = book.xpath('div/p[1]/a/text()').extract().pop()
                        item['comments'] = book.xpath('div/p[3]/').extract().pop()
                        item['time'] = book.xpath('div/div/p[2]').extract().pop().split()[2]
                        item['author'] = book.xpath('div/div[@class="publisher_info"]/p[1]/a').re(r'title=*(.*)')[0].split('>')[0]
                        item['publish'] = book.xpath('div/div/p[3]/a/text()').extract().pop()
                        item['price'] = book.xpath('div/p[6]/span[1]/text()').pop()
                        item['discount'] = book.xpath('div/p[6]/span[3]/text()').pop()
                        item['category1'] = response.meta["ID2_name"]  # 种类(小)
                        item['category2'] = response.meta["ID1_name"]  # 种类(大)
                    except Exception:
                        pass
                    yield item
            except Exception:
                pass