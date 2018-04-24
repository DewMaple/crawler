# coding:utf-8
import argparse
import itertools
import os
import re
import urllib
import urllib.parse

import requests
from img_utils.files import images_in_dir

str_table = {
    '_z2C$q': ':',
    '_z&e3B': '.',
    'AzdH3F': '/'
}

char_table = {
    'w': 'a',
    'k': 'b',
    'v': 'c',
    '1': 'd',
    'j': 'e',
    'u': 'f',
    '2': 'g',
    'i': 'h',
    't': 'i',
    '3': 'j',
    'h': 'k',
    's': 'l',
    '4': 'm',
    'g': 'n',
    '5': 'o',
    'r': 'p',
    'q': 'q',
    '6': 'r',
    'f': 's',
    'p': 't',
    '7': 'u',
    'e': 'v',
    'o': 'w',
    '8': '1',
    'd': '2',
    'n': '3',
    '9': '4',
    'c': '5',
    'm': '6',
    '0': '7',
    'b': '8',
    'l': '9',
    'a': '0'
}
char_table = {ord(key): ord(value) for key, value in char_table.items()}


# 解码
def decode(url):
    for key, value in str_table.items():
        url = url.replace(key, value)
    return url.translate(char_table)


# 百度图片下拉
def build_urls(word_):
    word_ = urllib.parse.quote(word_)
    url = r"http://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&fp=result&queryWord={word}&cl=2&lm=-1&ie=utf-8&oe=utf-8&st=-1&ic=0&word={word}&face=0&istype=2nc=1&pn={pn}&rn=60"
    urls = (url.format(word=word_, pn=x) for x in itertools.count(start=0, step=60))

    return urls


re_url = re.compile(r'"objURL":"(.*?)"')


# 获取imgURL
def resolve_image_url(html):
    img_urls = [decode(x) for x in re_url.findall(html)]
    return img_urls


# 下载图片
def download(img_url, dir_path, img_name):
    filename = os.path.join(dir_path, img_name)
    try:
        res = requests.get(img_url, timeout=15)
        if str(res.status_code)[0] == '4':
            print(str(res.status_code), ":", img_url)
            return False
    except Exception as e:
        print('抛出异常:', img_url)
        print(e)
        return False

    with open(filename, 'wb') as f:
        f.write(res.content)
    return True


def mk_dir(dir_name):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    return dir_name


def read_keywords(keywords_file):
    with open(keywords_file) as fp:
        keywords_ = fp.read().split("\n")
    return keywords_


def download_by_keyword(word_, base_dir, num_images):
    urls = build_urls(word_)
    base_dir = mk_dir(os.path.join(base_dir, word_))
    if len(images_in_dir(base_dir)) > 0:
        print('Has downloaded of {} '.format(word_))
        return
    idx = 0
    print('==' * 20, word_, '==' * 20)
    for url in urls:
        print("正在请求：", url)
        content = requests.get(url, timeout=10).content
        try:
            html = content.decode('utf-8')
        except Exception:
            html = content.decode('ISO-8859-1')

        img_urls = resolve_image_url(html)
        if len(img_urls) == 0:
            break

        for uri in img_urls:
            suffix_name = '{0:04d}'.format(idx)
            image_name = '{}_{}.{}'.format(word_, suffix_name, 'jpg')
            idx += 1
            if download(uri, base_dir, image_name):
                print("{}, 已下载 {} 张".format(word_, idx))
            else:
                break
            if idx >= num_images or idx > 9999:
                break
        if idx >= num_images:
            print('您一共下载了{}, {} 张图片'.format(word_, idx))
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--images_dir', type=str, help='Path to the downloaded directory.', default='crawled_images')
    parser.add_argument('--keywords_file', type=str, help='File contains the keywords that want to search.',
                        default='../celebrities')
    parser.add_argument('--max_num_images', type=int, help='Max number of images will download for each keyword',
                        default=200)
    args = parser.parse_args()
    images_dir = args.images_dir
    mk_dir(images_dir)
    keywords = read_keywords(args.keywords_file)

    print("= = " * 25)
    for word in keywords:
        download_by_keyword(word, images_dir, 300)
