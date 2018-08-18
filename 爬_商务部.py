# -*- coding: utf-8 -*-
"""
Created on Sat Mar 24 20:22:43 2018

@author: wn006
"""

import requests
from bs4 import BeautifulSoup 
from selenium import webdriver
import re,os

#%%
driver = webdriver.Chrome()#生成一个浏览器窗口
driver.get('http://interview.mofcom.gov.cn/mofcom_interview/front/blgg/list')
#打开链接并获取源代码

#%%
#------------------挑出总共的页码数----------------------------------
page_num_text = driver.find_element_by_css_selector('form table tr>td>b>font').text
pages_num = re.search('\d+' , page_num_text).group()
pages_num = int(pages_num)


all_news_link = []#用来存储所有的新闻链接
while True:
    links = driver.find_elements_by_css_selector('div.BL-list01.mt10 ul a')#用css选择器找出所有的文件
    news_link = []
    for link in links:#找到所有非英文版的链接
        if link.text not in  ['[英文版]' , '[政策解读]']:
            news_link.append(link.get_attribute('href'))
    all_news_link += news_link #添加到总库里
    page_num_text_ = driver.find_element_by_css_selector('form table tr>td>b>font').text
    current_page = int(re.findall('\d+' , page_num_text_)[1])#获取当前页面
    if len(news_link) != 15:
        print(current_page,len(news_link))
    if current_page >= pages_num:
        print(current_page,pages_num)
        break
    driver.find_element_by_id('nextPage').click()#找到下一页，模拟点击事件
driver.close()
#------------上边的程序基本没问题了，只是还会多出来一些--------需要把那些情况考虑到------

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
def save_to_txt(url_name, body):#把网页内容输出到txt文档
    fh = open(url_name + 'd.txt', 'w')
    fh.write(body)
    fh.close()

#%%
j = 136
error_url = []
for url in all_news_link[j:]:
    print(j)
    try:
        os.chdir(r'C:\Users\wn006\Desktop\商务部文件')
        html = requests.get(url).content.decode('utf-8')
        bsObj = BeautifulSoup(html , 'lxml')
        url_name = bsObj.select('h4#artitle')[0].text#提取名称
        url_name = re.sub('[\/:*?"<>|]' , "" , url_name) 
        #去除掉Windows系统中不允许作为文件名的字符
        bs_body = bsObj.select('div#zoom')[0] #提取正文
    
        body = bs_body.text #提取正文的文字部分
    
    #    body = body.replace('\xa0' , ' ') #把'\xa0'型空格换成' '型空格
    #    body = "\n".join(body.split('\u3000'))#把'\u3000'型换行符换成"\n"型换行符
    #    
        body = body.encode('gb2312' , errors = 'ignore').decode('gb2312' , errors='ignore')
    
        save_to_txt(url_name , body)
    
        #att_1 = re.search('.*附件：\u3000*(.*[\xa0\u3000])*商务部\xa0*' , body)
    
        body_html = bs_body.encode('utf-8').decode('utf-8')
    
        att_2 = re.search('.*附件：(.*)\d\d\d\d年\d{1,2}月\d{1,2}日' , body_html)
        if att_2 == None:
            attachment_name = []
            attachment_url = []
        else:
            att_2 = att_2.group(1)
            #直接找出后面那部分的文本，然后再提取链接
            attachment_url = re.findall('href="([^"]*)"' , att_2) #nice!找全了
            #接下来根据这些链接的属性来找到其名称
            attachment_url = [a_url for a_url in attachment_url if 
                              bs_body.select('a[href=%s]' %a_url)[0].text != "" 
                              and a_url.startswith('http')]
         
            attachment_name = [bs_body.select('a[href=%s]' %a_url)[0].text for a_url in attachment_url]
    
        os.chdir(r'C:\Users\wn006\Desktop\商务部文件\附件')
        if url_name not in os.listdir():
            os.mkdir(url_name)
        os.chdir(r'C:\Users\wn006\Desktop\商务部文件\附件\%s' % url_name)
        for i in range(len(attachment_name)):#用循环把附件全都下载到指定文件夹
            file_name = attachment_name[i]
            pdf_url = attachment_url[i]
            save_pdf(pdf_url , file_name)
        
    except:
        error_url.append(url)
    else:
        j += 1
    
#%%
os.chdir(r'C:\Users\wn006\Desktop')
save_to_txt("无法自动下载的网页链接" , json.dumps(error_url))








