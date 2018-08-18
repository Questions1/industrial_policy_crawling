# -*- coding: utf-8 -*-
"""
Created on Sat Aug  4 15:02:08 2018

@author: wn006
"""

import requests
from bs4 import BeautifulSoup 
from selenium import webdriver
import re
import os
import pandas as pd
import random as rd
import time
import json

#%%----------生成一个浏览器窗口,进入网站
options = webdriver.ChromeOptions()
options.add_argument('lang=zh_CN.UTF-8')
options.add_argument('user-agent="MQQBrowser/26 Mozilla/5.0 '\
                     '(Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22;'\
                     'CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko)'\
                     'Version/4.0 Mobile Safari/533.1"')

driver = webdriver.Chrome(chrome_options = options)
driver.get('http://xxgk.miit.gov.cn/gdnps/wjfbindex.jsp')

#%%获取所有文件页面的链接，存到一个列表里

all_news_link = []#用来存储所有的新闻链接
error_page_num = []
while True:
    page_num = driver.find_element_by_css_selector('td#allPageId')
    page_num_text = page_num.text.rsplit(" " , maxsplit=1)[1]
    
    current_page_num = int(page_num_text.rsplit("/")[0])
    sum_page_num = int(page_num_text.rsplit("/")[1])
    
    print('当前页码:%s , 总页码:%s'  %(current_page_num , sum_page_num))
    
    links = driver.find_elements_by_css_selector('tbody#contentBody a')
    all_news_link += [link.get_attribute('href') for link in links]
    if len(links) != 10 :
        print("------------------------ %s 页链接数量为 %s ：" 
              %(current_page_num,len(links)))
    if current_page_num >= sum_page_num:
        break
    time.sleep(5 + 5 * rd.random())
    while True:
        try:
            driver.find_element_by_link_text('下一页').click()
            time.sleep(10 + 5 * rd.random())
            break
        except:
            if current_page_num not in error_page_num:
                error_page_num.append(current_page_num)
        time.sleep(10 + 5 * rd.random())

driver.close() 
   
#%%
def save_to_txt(url_name, body):#把网页内容输出到txt文档
    fh = open(url_name + '.txt', 'w')
    fh.write(body)
    fh.close()
#%%
os.chdir(r'C:\Users\wn006\Desktop\工信部_爬虫')
save_to_txt("all_news_link" , json.dumps(all_news_link))
save_to_txt("error_page_num" , json.dumps(error_page_num))

#%%
fh = open("all_news_link" + '.txt', 'r')
content = fh.read()
fh.close()
all_news_link = json.loads(content)
#%%
#---------------下边把上边爬取的链接一个个下载网页并解析，提取需要的文本----------------
headers = {'User-Agent': 'Mozilla/5.0 ' +
           '(Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0'}
#先设置好请求头，防止反爬虫
def save_pdf(pdf_url , file_name): #定义下载pdf的函数
    response = requests.get(pdf_url,headers=headers)#获取响应
    with open(file_name,"wb") as pdf_file:  #这部分下载pdf的地方还是得好好理解一把呀！
        #另外参考一下人家的爬虫代码，提高提高
        for content in response.iter_content():
            pdf_file.write(content)
    print("Sucessful to download" + " " + file_name)

#%%
j = 450
error_url = []
#for url in all_news_link[j:]:
for url in error_url[j:]:
    print('当前位置：%s , 总长度：%s' %(j, len(error_url)))
    try:
        os.chdir(r'C:\Users\wn006\Desktop\工信部_爬虫\工信部文件')
        html = requests.get(url).content.decode('utf-8')
        bsObj = BeautifulSoup(html , 'lxml')
        url_name = bsObj.select('div.ctitle > h1')[0].text#提取名称
        url_name = re.sub('[\/:*?"<>|]' , "" , url_name) 
        #去除掉Windows系统中不允许作为文件名的字符
        bs_body = bsObj.select('div#con_con')[0] #提取正文
    
        body = bs_body.text #提取正文的文字部分
    
    #    body = body.replace('\xa0' , ' ') #把'\xa0'型空格换成' '型空格
    #    body = "\n".join(body.split('\u3000'))#把'\u3000'型换行符换成"\n"型换行符
    #    
        body = body.encode('gb2312' , errors = 'ignore').decode('gb2312' , errors='ignore')
    
        save_to_txt(url_name , body)
    
        #att_1 = re.search('.*附件：\u3000*(.*[\xa0\u3000])*商务部\xa0*' , body)
    
        body_html = bs_body.encode('utf-8').decode('utf-8')
    
        att_2 = re.search('.*附件：(.*)$' , body_html)
        if att_2 == None:
            attachment_name = []
            attachment_url = []
        else:
            att_2 = att_2.group(1)
            #直接找出后面那部分的文本，然后再提取链接
            attachment_url = re.findall('href="([^"]*)"' , att_2) #nice!找全了
            #接下来根据这些链接的属性来找到其名称
            attachment_url = [a_url for a_url in attachment_url if 
                              bs_body.select('a[href=%s]' %a_url)[0].text != ""]
         
            attachment_name = [bs_body.select('a[href=%s]' %a_url)[0].text for a_url in attachment_url]
            
            attachment_url = ['http://www.miit.gov.cn/' + a_url.rsplit('../' , 1)[1] for 
                              a_url in attachment_url]
        os.chdir(r'C:\Users\wn006\Desktop\工信部_爬虫\工信部文件\附件')
        if url_name not in os.listdir():
            os.mkdir(url_name)
        os.chdir(r'C:\Users\wn006\Desktop\工信部_爬虫\工信部文件\附件\%s' % url_name)
        for i in range(len(attachment_name)):#用循环把附件全都下载到指定文件夹
            file_name = attachment_name[i] + '.' + attachment_url[i].rsplit('.' , 1)[1]
            pdf_url = attachment_url[i]
            save_pdf(pdf_url , file_name)
        
    except:
        error_url.append(url)
    
    j += 1
    #time.sleep(1 + rd.random())
    

os.chdir(r'C:\Users\wn006\Desktop\工信部_爬虫')
save_to_txt("无法自动下载的网页链接" , json.dumps(error_url))
#%%
