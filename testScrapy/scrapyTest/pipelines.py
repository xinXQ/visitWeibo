# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
from scrapy import log
from twisted.enterprise import adbapi
import MySQLdb.cursors
from scrapy.utils.project import get_project_settings
from MySQLdb import IntegrityError

# conn = MySQLdb.connect(host='192.168.223.1', port=3306, user='root', passwd='root', db='test',charset='utf8', use_unicode=False)
# cur = conn.cursor()
class ScrapytestPipeline(object):
    
    def __init__(self):
        settings = get_project_settings()
        # 初始化一个数据库连接池
        self.dbpool = adbapi.ConnectionPool(
        dbapiName='MySQLdb',
        host=settings.get("MYSQL_HOST","127.0.0.1"),
        db = settings.get("MYSQL_DB","test"),
        user = settings.get("MYSQL_USERNAME","root"),
        passwd = settings.get("MYSQL_PASSWD","root"),
        cursorclass = MySQLdb.cursors.DictCursor,
        charset = 'utf8',
        use_unicode = False
    )
    
    def process_item(self, item, spider):
        try:
            query = self.dbpool.runInteraction(self._conditional_insert, item)
            log.msg("success to save %s"%item['title'], log.INFO)
        except Exception,e:
            log.msg("fail to save %s"%item['url'], log.ERROR)
        return item
    
    
    def drop_url_parameter(self,url):
        if url.find('/?') != -1 or url.find('html?') != -1 or url.find('htm?') != -1:
            return url[0:url.find('?')]
        elif url.find('#') != -1:
            return url[0:url.find('#')]
        else:
            return url
    
    
    # 保存记录到数据库
    def _conditional_insert(self, tx, item):
        sql = "insert into network_media (cityId,keywordId,url,title,content,postTime,source) values ('%d','%d','%s','%s','%s','%s','%s')"
        try:
            # 对url做处理
            url = self.drop_url_parameter(item['url'])
            tx.execute(sql%(int(item['city_id']),int(item['keyword_id']),url,item['title'],item['content'],item['post_time'].strftime('%Y-%m-%d %H:%M:%S'),item['source']))
        except IntegrityError,ie:
            log.msg("get same url %s , and drop it"%item['url'], log.ERROR)
        