
import requests
from bs4 import BeautifulSoup
import re
import os
import json
import random as rd
import time

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


if __name__ == '__main__':
    """
    在这里插入伪代码
    """


def save_to_txt(path, url_name, body):  # 把网页内容输出到txt文档
    """
    两个用途：一个是把提取到的all_news_link输出，
    另一个是把从网页上提取到的正文内容输出
    :param url_name: 输出的文件名称
    :param body: 文件包含的内容
    """
    fh = open(os.path.join(path, url_name), 'w')
    fh.write(body)
    fh.close()


def save_attach(pdf_url, file_name):  # 定义下载pdf的函数
    """
    这个函数还缺少一个输出路径的参数，之后要下载附近的时候得补上

    把附件都下载下来(似乎是不仅可以下载pdf，所有附件都可以下载?)
    :param pdf_url: 附件链接
    :param file_name: 输出的附件名称
    """
    # 先设置好请求头，防止反爬虫
    headers = "User-Agent':'Mozilla/5.0 \
    (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0"
    response = requests.get(pdf_url, headers=headers)  # 获取响应
    with open(file_name, "wb") as pdf_file:  # 这部分下载pdf的地方还是得好好理解一把呀！
        for content in response.iter_content():
            pdf_file.write(content)
    print("Successfully to download" + " " + file_name)


def read_news_link(all_path):
    """
    把第一步提取到的all_news_link重新读取进来
    :param all_path: all_news_link所在位置
    """
    fh = open(all_path, 'r')
    content = fh.read()
    fh.close()
    all_news_link = json.loads(content)
    return all_news_link


# 这部分来提取all_news_link和error_page_num
if __name__ == '__main__':
    # 打开浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('lang=zh_CN.UTF-8')
    options.add_argument('user-agent="MQQBrowser/26 Mozilla/5.0 \
    (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) \
    AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"')
    driver = webdriver.Chrome(chrome_options=options)

    driver.get('http://www.chinatax.gov.cn/n810341/n810755/index.html')

    # 获取所有文件页面的链接，存到一个列表里
    all_news_link = []  # 用来存储所有的新闻链接
    error_page_num = []
    while True:
        page_num = driver.find_element_by_css_selector('div.sv_lcon  table.pageN')
        current_page_num = int(page_num.find_element_by_css_selector('font[color = "red"]').text)
        sum_page_num = int(page_num.text.split('总页数:')[1])

        print('当前页码:%s , 总页码:%s' % (current_page_num, sum_page_num))

        links = driver.find_elements_by_css_selector('div.sv_lcon > div.column dl a')
        # 用css选择器找出所有的文件

        all_news_link += [link.get_attribute('href') for link in links]

        if len(links) != 25:
            print("------------------------ %s 页链接数量为 %s ："
                  % (current_page_num, len(links)))
        if current_page_num >= sum_page_num:
            break
        while True:
            try:
                driver.find_element_by_link_text('下页').click()
                time.sleep(10 + 5 * rd.random())
                break
            except:
                if current_page_num not in error_page_num:
                    error_page_num.append(current_page_num)
            time.sleep(10 + 5 * rd.random())

    driver.close()

    save_to_txt('./crawled_file/国家税务总局/', '国家税务总局_all_news_link.txt',
                json.dumps(all_news_link))
    save_to_txt('./crawled_file/国家税务总局/', '国家税务总局_error_page_num.txt',
                json.dumps(error_page_num))


if __name__ == '__main__':
    all_path = os.path.join("./crawled_file/国家税务总局/", "国家税务总局_all_news_link.txt")
    all_news_link = read_all_news_link(all_path)
    success_url = []  # 把爬成功的url也记录下来
    nested_url = []  # 有些url使用window.location.href重定向，需要使用selenium来爬
    j = 0
    # for url in all_news_link[j:]:
    for url in all_news_link:
        j += 1
        print('当前位置：%s , 总长度：%s, 剩余：%s' % (j, len(all_news_link), len(all_news_link) - j))
        try:
            headers = {"Accept": "text/html,application/xhtml+xml,application/xml;",
                       "Accept-Encoding": "gzip",
                       "Accept-Language": "zh-CN,zh;q=0.8",
                       "Referer": "http://www.example.com/",
                       "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) \
                       AppleWebKit/537.36 (KHTML, like Gecko) \
                       Chrome/42.0.2311.90 Safari/537.36"}
            html = requests.get(url, headers=headers).content.decode('utf-8')

            # 判断是否是嵌套网页
            tmp = re.search(r".+(window.location.href='%s).+" % url, html)
            if tmp is not None:
                nested_url.append(url)

            # 使用BeautifulSoup解析网页
            bsObj = BeautifulSoup(html, 'lxml')

            # 提取文件名
            url_name = bsObj.select('ul.sv_textcon li.sv_texth1_red')[0].text  # 提取名称
            url_name = re.sub('[\/:*?"<>|]', "", url_name)  # 去除掉Windows系统中不允许作为文件名的字符

            # 提取正文
            bs_body = bsObj.select('li#tax_content')[0]
            body = bs_body.text  # 提取正文的文字部分
            body = body.encode('gb2312', errors='ignore').decode('gb2312', errors='ignore')

            # 输出正文内容并记录
            save_to_txt('./crawled_file/国家税务总局/正文/', '%s.txt' % url_name, body)
            success_url.append(url)
        except:
            pass
            # all_news_link.append(url)
        # time.sleep(1 + rd.random())
    save_to_txt('./crawled_file/国家税务总局/', '国家税务总局_nested_url.txt',
                json.dumps(nested_url))
    save_to_txt('./crawled_file/国家税务总局/', '国家税务总局_success_url.txt',
                json.dumps(success_url))


# requests处理得似乎太好，用selenium
if __name__ == '__main__':
    all_path = os.path.join("./crawled_file/国家税务总局/", "国家税务总局_all_news_link.txt")
    all_news_link = read_news_link(all_path)
    success_url_path = os.path.join("./crawled_file/国家税务总局/", "国家税务总局_success_url.txt")
    success_url = read_news_link(success_url_path)

    left_url = list(set(all_news_link).difference(set(success_url)))
    new_success_url = []  # 把这次爬成功的url也记录下来
    j = 0

    options = webdriver.ChromeOptions()
    options.add_argument('lang=zh_CN.UTF-8')
    options.add_argument('user-agent="MQQBrowser/26 Mozilla/5.0 \
        (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) \
        AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"')
    driver = webdriver.Chrome(chrome_options=options)

    for url in left_url[:20]:
        j += 1
        print('当前位置：%s , 总长度：%s, 剩余：%s' % (j, len(all_news_link), len(all_news_link) - j))
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id("tax_content"))

            # 提取文件名
            url_name = driver.find_element_by_css_selector('ul.sv_textcon li.sv_texth1_red').text
            url_name = re.sub('[\/:*?"<>|]', "", url_name)  # 去除掉Windows系统中不允许作为文件名的字符

            # 提取正文
            se_body = driver.find_element_by_css_selector('li#tax_content')  # 提取正文
            body = se_body.text  # 提取正文的文字部分
            body = body.encode('gb2312', errors='ignore').decode('gb2312', errors='ignore')

            # 输出正文内容并记录
            save_to_txt('./crawled_file/国家税务总局/正文/', '%s.txt' % url_name, body)
            success_url.append(url)
        except:
            pass

    update_success_url = list(set(success_url).union(set(new_success_url)))
    save_to_txt('./crawled_file/国家税务总局/', '国家税务总局_success_url.txt',
                json.dumps(update_success_url))
