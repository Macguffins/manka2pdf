import sys
import re
import urllib3
import os
import argparse
import pdfkit
from bs4 import BeautifulSoup
from pg import DB
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4



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
        arg_path = os.path.abspath(args.path) + '/'
    if args.update:
        arg_update = True
    else:
        arg_update = False
    return (arg_page, arg_id, arg_path, arg_update)


def update_index(host, home, path, db, http=None, flag=False):
    if not http:
        http = urllib3.PoolManager()
    html = http.request('GET', host + home)
    soup = BeautifulSoup(html.data.decode('utf-8'), features='html5lib' )
    for x in soup.find_all('a'):
        if not x.string:
            continue
        if str.strip(x.string) == '末页':
            s = x['href']
            match_obj = re.match(r'list_4_([0-9]*).*', s) 
            if match_obj:
                max_page = int(match_obj.group(1))
                break
    cnt = 0
    for page in range(1, max_page + 1):
        page_str = 'list_4_' + str(page) + '.html'
        rsp = http.request('GET', host+home+'/'+page_str)
        soup = BeautifulSoup(rsp.data.decode('utf-8'), features='html5lib')
        for dtag in soup.find_all('div'):
            if dtag.has_attr('class') and dtag['class'] == ['c_inner']:
                for atag in dtag.find_all('a'):
                    if not atag.has_attr('href') or not atag.has_attr('title'):
                        continue
                    href = atag['href']
                    mid = re.match(r'.*/([0-9]+).html', href).group(1)
                    mid = int(mid)
                    title = atag['title']
                    img = atag.img
                    src = img['src']
                    if not re.search('yaoqi', src):
                        continue
                    if os.access(path + title + '.pdf', os.F_OK):
                        download_flag = True
                    else:
                        download_flag = False
                    db.upsert('comic_info', {'id':mid, 'name':title, 'url':host + href[1:], 'img_url':src, 'download':download_flag})
                    cnt += 1
    return cnt

def get_info_by_id(m_id, db):
    result = db.query(f"select * from comic_info where id = {m_id:d} and disable = false")
    if not result.ntuples():
        return None
    return result.dictresult()

def download_manka(dic, db):
    page = 0
    match_obj = re.match(f'(.*)(\..*)', dic['img_url'])
    head = match_obj.group(1)
    tail = match_obj.group(2)
    c = None
    if dic['img_url'] != str.strip(dic['img_url']):
        print('NOT EQ')
        exit(0)
    c = Canvas(dic['name'] + '.pdf')
    try:
        while True:
            page += 1
            print(f'Downloading Page{page}')
            image = ImageReader(f'{head}{page:d}{tail}')
            c.setPageSize(image.getSize())
            c.drawImage(image, 0, 0, mask='auto')
            c.showPage()
    except OSError:
        if page == 1:
            return 0
        pass
    page -= 1
    if c:c.save()
    print('Done')
    return page

def update_after_download(m_id, path, page, disable, db):
    db.update('comic_info', {'download':True, 'download_path':path,'total_pages':page, 'favour':True, 'disable':disable}, id = m_id)
    return


if __name__ == '__main__':
    print('test start')
    host = 'http://m.yaoqi520.cc/'
    home = 'shaonvmanhua/'
    db = DB()
    update_index(host, home)
