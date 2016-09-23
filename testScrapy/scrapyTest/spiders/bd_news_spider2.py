#coding:utf-8

from scrapy.spider import Spider
from scrapy.selector import Selector
import scrapy
from scrapy.utils.project import get_project_settings
from scrapyTest.items import ScrapytestItem
from scrapy import log
from scrapy.mail import MailSender
import MySQLdb
import datetime

class BDNewsSpider2(Spider):
    # 一个爬虫的标识，必须是唯一的
    name = "baidu_news_spider_huawei"
    
    # 这些都需要读取数据库来初始化
    citys = {}
    keywords = {}
    raw_url = "http://news.baidu.com/ns?cl=2&s=1&tn=newsdy&ct1=0&ct=0&rn=50&class=0&q1=keyword&pn=0"
    max_datetime = None
    
    # 本模块的常量
    # 本模块需要的sql
    max_datetime_sql = "select max(posttime) from network_media"
    select_citys_sql = "select id,name from city"
    select_keywords_sql = "select id,keyword from keyword"
    spider_start_time = "2015-09-01 00:00:00"
    
    
    def get_max_post_datetime(self):
        settings = get_project_settings()
        conn = MySQLdb.connect(host=settings.get("MYSQL_HOST","192.168.223.1"), port=settings.getint("MYSQL_PORT",3306), user=settings.get("MYSQL_USERNAME","root"), passwd=settings.get("MYSQL_PASSWD","root"), db=settings.get("MYSQL_DB","root"),charset='utf8', use_unicode=False)
        cur = conn.cursor()
        cur.execute(self.max_datetime_sql)
        data = cur.fetchone()
        conn.close()
        if data[0] == None:
            return datetime.datetime.strptime(self.spider_start_time, "%Y-%m-%d %H:%M:%S") 
        return data[0]
        
    
    def read_keyword_city(self):    
        settings = get_project_settings()
        conn = MySQLdb.connect(host=settings.get("MYSQL_HOST","192.168.223.1"), port=settings.getint("MYSQL_PORT",3306), user=settings.get("MYSQL_USERNAME","root"), passwd=settings.get("MYSQL_PASSWD","root"), db=settings.get("MYSQL_DB","root"),charset='utf8', use_unicode=False)
        cur = conn.cursor()
        cur.execute(self.select_citys_sql)
        results = cur.fetchall()
        for row in results:
            self.citys[row[1]] = row[0]
        
        cur = conn.cursor()
        cur.execute(self.select_keywords_sql)
        results = cur.fetchall()
        for row in results:
            self.keywords[row[1]] = row[0]
        conn.close()
        
        
    def start_requests(self):
        # 首先查询出最新的时间，时间是判断是否继续抓取的条件
        self.max_datetime = self.get_max_post_datetime()
        # 读取数据库中的关键词和省市,拼装首页
        self.read_keyword_city()
        city_join_keyword = [((' '.join((keyword,city))).replace(' ','+'),(keyword_id,city_id)) for keyword,keyword_id in self.keywords.items() for city,city_id in self.citys.items()]
        start_requests = []
        for x in city_join_keyword:
            request = scrapy.Request(self.raw_url.replace("keyword",x[0]),callback=self.parse)
            request.meta['keyword_id'] = x[1][0]
            request.meta['city_id'] = x[1][1]
            start_requests.append(request)
        return start_requests
    
    
    def time_translate(self,time_str):
        # 7分钟前  1小时前 2016年08月24日 18:26
        # 1小时前 u'1\u5c0f\u65f6\u524d'
        # u'58\u5206\u949f\u524d'
        result_time = None
        now = datetime.datetime.now()
        if time_str.find(u'\u5c0f\u65f6') != -1:
            # 小时的处理
            time_num = int(time_str.split(u'\u5c0f\u65f6')[0])
            result_time = now - datetime.timedelta(hours=time_num)
        elif time_str.find(u'\u5206\u949f') != -1:
            # 分钟的处理
            time_num = int(time_str.split(u'\u5206\u949f')[0])
            result_time = now - datetime.timedelta(minutes=time_num)
        else:
            # 2016年08月24日 18:26 的处理
            year = int(time_str[0:4])
            month = int(time_str[5:7])
            day = int(time_str[8:10])
            hour = int(time_str[12:14])
            mini = int(time_str[15:17])
            result_time = datetime.datetime(year,month,day,hour,mini)
        # 判断是都继续翻页
        spider_enable = True
        if result_time < self.max_datetime:
            spider_enable = False 
        return result_time,spider_enable
    
    
    def parse(self, response):
        try:
            keyword_id = response.meta['keyword_id']
            city_id = response.meta['city_id']
            select = Selector(response)
            spider_enable = True
            # 解析出新闻的标题、时间、正文
            sites = select.xpath('//div[@class="result"]')
            for site in sites:
                item = ScrapytestItem()
                item['city_id'] = city_id
                item['keyword_id'] = keyword_id
                item['url'] = site.xpath('h3/a/@href').extract()[0]
                item['title'] = ''.join(site.xpath('h3/a/text() | h3/a/em/text()').extract())
                content_selector = [x.extract() for x in site.xpath('div//p/parent::*/text()')]
                item['content'] = ''.join(content_selector)
                from_and_time = site.xpath('div//p/text()').extract()[0]
                times = from_and_time.split(u'\xa0')
                item['source'] = times[0]
                item['post_time'] = self.time_translate(times[-1])[0]
                spider_enable = self.time_translate(times[-1])[1]
                # 处理时间 7分钟前  1小时前 2016年08月24日 18:26
                if spider_enable:
                    yield item
            # 如果本页是最后一页吗，也是需要停止的
            if len(sites) != 50:
                spider_enable = False
            # 解析出下一页的url，特别注意,最后一页
            if spider_enable:
                current_url = response.url
                page_num = int(current_url.split('pn=')[-1])
                next_url = current_url.replace('pn='+str(page_num),'pn='+str(page_num+50))
                # next_url
                request = scrapy.Request(next_url, callback=self.parse)
                request.meta['keyword_id'] = keyword_id
                request.meta['city_id'] = city_id
                yield request
            else:
                log.msg("spider for %s is end"%response.url, level=log.INFO)
            log.msg("success to parse : %s"%response.url, level=log.INFO)
        except KeyError,e:
            log.msg("fail to prase url : %s"%response.url,level=log.ERROR)
            log.msg(e, level=log.ERROR)
            print e
            # mailer = MailSender(smtphost="smtp.163.com",mailfrom="18232184201@163.com",smtpuser="18232184201@163.com",smtppass="zxd521",smtpport=25)
            # mailer.send(to=["work4dong@163.com"], subject="Some subject", body=response.url)

