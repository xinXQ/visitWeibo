#coding:utf-8

from scrapy.spider import Spider
from scrapy.selector import Selector
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy import log
from scrapy.mail import MailSender
import MySQLdb
import re
import urllib
import datetime


class Spider4Beijing(Spider):
    # 一个爬虫的标识，必须是唯一的
    name = "spider_for_beijing"
    
    start_urls = ["http://www.bjda.gov.cn/bjfda/gzdt14/tzgg/tz/750afccd-1.html"]
    min_datetime = datetime.datetime(2015,9,1)
    
    def __init__(self):
        settings = get_project_settings()
        self.conn = MySQLdb.connect(host=settings.get("MYSQL_HOST","192.168.223.1"), port=settings.getint("MYSQL_PORT",3306), user=settings.get("MYSQL_USERNAME","root"), passwd=settings.get("MYSQL_PASSWD","root"), db=settings.get("MYSQL_DB","root"),charset='utf8', use_unicode=False)
        
    
    def parse(self, response):
        item_urls = response.xpath('//*[@id="750afccda0914223ae6d51fa450e7b80"]/div[2]/ul/li/span[1]/a/@href').extract()
        for item_url in item_urls:
            yield scrapy.Request("http://www.bjda.gov.cn"+item_url,callback=self.parseItem)
        if len(item_urls) != 0:
            current_url = response.url
            yield scrapy.Request(current_url[:53]+str(int(re.search("50afccd-(\d+)\.html", current_url).group(1))+1)+".html",callback=self.parse)
            
            
            
    def parseItem(self,response):
        try:
            url = response.url
            title = response.xpath('//*[@id="container"]/table/tbody/tr[1]/td/h1/text()').extract()[0]
            content = ''.join(response.xpath('//*[@id="container"]/table/tbody/tr[3]')[0].xpath('string(.)').extract())
            postTime_str = response.xpath('//*[@id="container"]/table/tbody/tr[2]/td/text()').extract()[0]
            postTime_arr = re.findall('\d+', postTime_str)
            postTime = datetime.datetime(int(postTime_arr[0]),int(postTime_arr[1]),int(postTime_arr[2]))
            view_num = urllib.urlopen("http://www.bjda.gov.cn/eportal/ui?pageId=132891&moduleId=3&columnId=133269&articleKey=%s&struts.portlet.action=/app/counting-front!saveInfo.action"%re.search('tz/(\d+)/index', url).group(1)).read()
            source = u"北京市食品药品监督管理局"
            if postTime > self.min_datetime:
                sql = "insert into gov_site (url,title,content,postTime,viewNum,source) values ('%s','%s','%s','%s',%d,'%s')"
                cur = self.conn.cursor()
                cur.execute(sql%(url,title,content,postTime.strftime('%Y-%m-%d %H:%M:%S'),int(view_num),source))
                self.conn.commit()
                log.msg('success to save %s'%title, log.INFO)
        except Exception,e:
            log.msg("parse gov %s fail "%response.url, log.ERROR)           
