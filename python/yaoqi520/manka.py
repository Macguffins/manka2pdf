import sys
import re
import urllib3
import os
import argparse
import pdfkit
from bs4 import BeautifulSoup
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter



host='http://m.yaoqi520.cc/'
home='shaonvmanhua/'
http = urllib3.PoolManager()

def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, help='您想看前几页的漫画？')
    parser.add_argument('--id', type=int, help='根据漫画id下载')
    parser.add_argument('--path', type=str, help='下载根目录')
    parser.add_argument('--update', type=str, help='是否更新索引文件')
    args = parser.parse_args()
    if args.max:
        if args.max <= 0:
            print('至少看一页吧')
            exit(0)
        arg_page = args.max
    else:
        arg_page = 1
    if args.id:
        arg_id = args.id
    else:
        arg_id = -1
    arg_path = os.getcwd() + '/'
    if args.path:
        if args.path[-1] == '/':
            arg_path = args.path
        else:
            arg_path = args.path + '/'
    if args.update:
        arg_update = True
    else:
        arg_update = False
    return (arg_page, arg_id, arg_path, arg_update)

def make_manka_file(arg_path):
    try:
        os.mkdir(arg_path + 'manka')
    except FileExistsError:
        pass
    os.chdir(arg_path + 'manka')
    return

def make_index_file(host, home):
    with open('index', 'w') as f:
            rsp = http.request('GET', host+home)
            soup = BeautifulSoup(rsp.data.decode('utf-8'))
            for x in soup.find_all('a'):
                if not x.string:continue
                if str.strip(x.string) == '末页':
                    s = x['href']
                    match_obj = re.match(r'list_4_([0-9]*).*', s) 
                    if match_obj:
                        max_page = int(match_obj.group(1))
                        break
            manka_id = 1
            for page in range(1, max_page + 1):
                page_str = 'list_4_' + str(page) + '.html'
                rsp = http.request('GET', host+home+'/'+page_str)
                soup = BeautifulSoup(rsp.data.decode('utf-8'))
                for dtag in soup.find_all('div'):
                    if dtag.has_attr('class') and dtag['class'] == ['c_inner']:
                        for atag in dtag.find_all('a'):
                            if not atag.has_attr('href') or not atag.has_attr('title'):
                                continue
                            f.write('id=' + str(manka_id) + '\n')
                            f.write('漫画名=' + atag['title'] + '\n')
                            f.write('链接=' + host + atag['href'][1:] + '\n')
                            manka_id += 1

def get_info_by_id(manka_id):
    with open('index') as f:
        for x in f:
            if x[:2] == 'id' and str.strip(x[3:]) == str(manka_id):
                manka_name = next(f)[4:]
                manka_link = next(f)[3:]
                return (manka_name, manka_link)
        print('找不见id为' + manka_id + '的漫画')
        exit(-1)

def get_pic_url(html):
    soup = BeautifulSoup(html.data)
    x = soup.find(id='imgString')
    if not x:
        print(soup.prettify())
        print('no imgString')
        exit(0)
    if not x.a and x.img:
        url = x.img['src']
    else:
        url = x.a.img['src']
    if not url:
        exit(0)
    return url



def download_manka(name, link):
    print('downloading ' + name + '...')
    http = urllib3.PoolManager()
    match_obj= re.match(r'(.*/)([0-9]+).html', link)
    html = http.request('GET', str.strip(link))
    l = get_pic_url(html)
    match_obj = re.match(r'(.*yaoqi)(.*).jpg', l)
    prefix = match_obj.group(1)
    soup = BeautifulSoup(html.data)
    for x in soup.find_all('a'):
        if x.string:
            match_obj = re.match(r'.*共([0-9]*)页.*', x.string)
            if match_obj:
                total = int(match_obj.group(1))
    for x in range(1, total + 1):
        if x == 1:
            image = ImageReader(prefix + str(x) + '.jpg')
            c = Canvas(str.strip(name) + '.pdf', pagesize=image.getSize())
            c.drawImage(image, 0, 0, width = image.getSize()[0], height = image.getSize()[1], mask='auto')
            c.showPage()
            continue
        image = ImageReader(prefix + str(x) + '.jpg')
        c.drawImage(image, 0, 0, width = image.getSize()[0], height = image.getSize()[1], mask='auto')
        c.showPage()
    c.save()
    return

last, m_id, path, update_flag = parse_arg()
make_manka_file(path)
if update_flag:
    make_index_file(host, home)
if m_id < 0:
    with open('index') as f:
        for i in range(0, last):
            x = next(f)
            if x[:2] == 'id':
                m_id = str.strip(x[3:])
                name = next(f)[4:]
                link = next(f)[3:]
                download_manka(name, link)
    exit(0)
name, link = get_info_by_id(str(m_id))
download_manka(str.strip(name), str.strip(link))
