#coding:utf-8

import MySQLdb
import urllib2
from lxml import etree
import lxml
from lxml import html
import re


#page = urllib2.urlopen("http://www.shfda.gov.cn/gb/node2/yjj/xxgk/zfxxgk/zxxxgk/sp/u1ai49118.html").read()
#url = "http://www.shfda.gov.cn/gb/node2/yjj/xxgk/zfxxgk/zxxxgk/sp/u1ai49068.html"
"""
conn = MySQLdb.connect(host="120.132.95.245", port=3306, user="ldp",passwd="lanCl0ud6062004",db="ldp_dfjh",charset='utf8', use_unicode=False)
while True:
    url = raw_input("url:")
    page = urllib2.urlopen(url).read()
    root=html.document_fromstring(page.decode('gb2312'))
    title = root.xpath('//*[@id="ivs_title"]/text()')[0]
    content = ''.join(root.xpath('//*[@id="ivs_content"]//text()'))
    post_time = root.xpath('//*[@id="example"]/h2/small[1]/text()')[0]
    view_num = re.search('\d+', urllib2.urlopen("http://www.shfda.gov.cn/PVStatist/GetCountByUrl.aspx?url="+url).read()).group()
    source = u'上海市食品药品监督管理局'

    cur = conn.cursor()
    sql = "insert into gov_site (url,title,content,postTime,viewNum,source) values ('%s','%s','%s','%s',%d,'%s')"
    cur.execute(sql%(url,title,content,post_time,int(view_num),source))
    conn.commit()
    print title
    print view_num
    print content
    print "============================"

"""
