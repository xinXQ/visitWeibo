#coding:utf-8

from scrapy.spider import Spider
from scrapy.selector import Selector
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy import log
from scrapy.mail import MailSender
import MySQLdb
import re

class BDNewsSpider4(Spider):
    # 一个爬虫的标识，必须是唯一的
    name = "baidu_news_post_num_spider"
    
    # 本模块的常量
    raw_url = "http://news.baidu.com/ns?from=news&cl=2&bt=1441036800&y0=2015&m0=9&d0=1&y1=2016&m1=8&d1=30&et=1472572799&q1=&submit=%B0%D9%B6%C8%D2%BB%CF%C2&q3=&q4=&mt=0&lm=&s=2&begin_date=2015-9-1&end_date=2016-8-30&tn=newsdy&ct1=0&ct=0&rn=50&q6="
    select_urls = "select distinct url from media_post_num"
    update_sql = "update media_post_num set postNum = %d where url = '%s'"
    urls = []
    conn = None
    
    def read_url(self):    
        settings = get_project_settings()
        self.conn = MySQLdb.connect(host=settings.get("MYSQL_HOST","192.168.223.1"), port=settings.getint("MYSQL_PORT",3306), user=settings.get("MYSQL_USERNAME","root"), passwd=settings.get("MYSQL_PASSWD","root"), db=settings.get("MYSQL_DB","root"),charset='utf8', use_unicode=False)
        cur = self.conn.cursor()
        cur.execute(self.select_urls)
        results = cur.fetchall()
        for row in results:
            self.urls.append(row[0])

        
    def start_requests(self):
        # 查询数据库中，所有需要抓取的域名
        self.read_url()
        start_requests = []
        for url in self.urls:
            request = scrapy.Request(self.raw_url+url,callback=self.parse)
            request.meta['db_id_url'] = url
            start_requests.append(request)
        return start_requests
    
    
    @staticmethod
    def close(spider, reason):
        return Spider.close(spider, reason)
    
    
    def parse(self, response):
        try:
            db_id_url = response.meta['db_id_url']
            select = Selector(response)
            find_str = select.xpath('//*[@id="header_top_bar"]/span/text()').extract()[0]
            result = int(''.join(re.findall('\d+', find_str)))
            cur = self.conn.cursor()
            cur.execute(self.update_sql%(result,db_id_url))
            self.conn.commit()
            log.msg("success to parse : %s and result is %s"%(response.url,find_str), level=log.INFO)
        except KeyError,e:
            log.msg("fail to prase url : %s"%response.url,level=log.ERROR)
            mailer = MailSender(smtphost="smtp.163.com",mailfrom="18232184201@163.com",smtpuser="18232184201@163.com",smtppass="zxd521",smtpport=25)
            mailer.send(to=["work4dong@163.com"], subject="Some subject", body=response.url)

