# encoding: utf-8

import socket
# 用于https加密
import ssl
# 用于下载的库
import requests
# lxml爬虫的库
from lxml import html
from utils import log


class Model(object):
    def __repr__(self):
        class_name = self.__class__.__name__
        properties = (u'{} = ({})'.format(k, v) for k, v in self.__dict__.items())
        # u 代表unicode
        r = u'\n<{}:\n  {}\n>'.format(class_name, u'\n  '.join(properties))
        return r


class Movie(Model):
    def __init__(self):
        self.ranking = 0
        self.cover_url = ''
        self.name = ''
        self.staff = ''
        self.publish_info = ''
        self.rating = 0
        self.quote = ''
        self.number_of_comments = 0


def parsed_url(url):
    """
    解析 url 返回 (protocol host port path)
    """
    # 检查协议
    protocol = 'http'
    if url[:7] == 'http://':
        u = url.split('://')[1]
    elif url[:8] == 'https://':
        protocol = 'https'
        u = url.split('://')[1]
    else:
        # '://' 定位 然后取第一个 / 的位置来切片
        u = url

    # 检查默认 path
    i = u.find('/')
    if i == -1:
        host = u
        path = '/'
    else:
        host = u[:i]
        path = u[i:]

    # 检查端口
    port_dict = {
        'http': 80,
        'https': 443,
    }
    # 默认端口
    port = port_dict[protocol]
    if host.find(':') != -1:
        h = host.split(':')
        host = h[0]
        port = int(h[1])

    return protocol, host, port, path


def socket_by_protocol(protocol):
    """
    根据协议返回一个 socket 实例
    """
    if protocol == 'http':
        s = socket.socket()
    else:
        # HTTPS 协议需要使用 ssl.wrap_socket 包装一下原始的 socket
        s = ssl.wrap_socket(socket.socket())
    return s


def response_by_socket(s):
    """
    参数是一个 socket 实例
    返回这个 socket 读取的所有数据
    """
    response = b''
    buffer_size = 1024
    while True:
        # 循环接收数据
        r = s.recv(buffer_size)
        if len(r) == 0:
            break
        response += r
    return response


def parsed_response(r):
    """
    把 response 解析出 状态码 headers body 返回
    状态码是 int
    headers 是 dict
    body 是 str
    """
    header, body = r.split('\r\n\r\n', 1)
    h = header.split('\r\n')
    status_code = h[0].split()[1]
    status_code = int(status_code)

    headers = {}
    for line in h[1:]:
        k, v = line.split(': ')
        headers[k] = v
    return status_code, headers, body


def get(url):
    """
    用 GET 请求 url 并返回响应
    """
    protocol, host, port, path = parsed_url(url)

    s = socket_by_protocol(protocol)
    s.connect((host, port))

    request = 'GET {} HTTP/1.1\r\nhost: {}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36\r\nConnection: close\r\n\r\n'.format(
        path, host)
    encoding = 'utf-8'
    s.send(request.encode(encoding))

    response = response_by_socket(s)
    # log('response', response)
    r = response.decode(encoding)

    status_code, headers, body = parsed_response(r)
    if status_code == 301:
        url = headers['Location']
        return get(url)
    return status_code, headers, body


def movie_from_div(div):
    movie = Movie()
    #             当前的路径 .代表前面定义的div元素，具体的属性是class="pic"，下面的em 生成的是一个列表
    movie.ranking = div.xpath('.//div[@class="pic"]/em')[0].text
    #                                                       src属性
    movie.cover_url = div.xpath('.//div[@class="pic"]/a/img/@src')
    names = div.xpath('.//span[@class="title"]/text()')
    movie.name = ''.join(names)
    movie.rating = div.xpath('.//span[@class="rating_num"]')[0].text
    quote_tag = div.xpath('.//span[@class="inq"]')
    # 存在没有quote的情况
    if len(quote_tag) is not 0:
        movie.quote = div.xpath('.//span[@class="inq"]')[0].text
    else:
        movie.quote = ''
    infos = div.xpath('.//div[@class="bd"]/p/text()')
    movie.staff, movie.publish_info = [i.strip() for i in infos[:2]]
    #                                                          用-1取最后一个
    movie.number_of_comments = div.xpath('.//div[@class="star"]/span')[-1].text[:-3]
    return movie


def movies_from_url(url):
    # _占位符 无意义 但必须存在
    _, _, page = get(url)
    # 将html中的body成一个特殊的类，表示html文档，得到xpath的方法用于查找数据
    root = html.fromstring(page)
    movie_divs = root.xpath('//div[@class="item"]')
    movies = [movie_from_div(div) for div in movie_divs]
    return movies


def download_covers(movies):
    '''
    将图片保存到文件夹中
    '''
    for m in movies:
        image_url = m.cover_url[0]
        r = requests.get(image_url)
        path = 'pic/' + m.name.split('/')[0] + '.jpg'
        with open(path, 'wb') as f:
            f.write(r.content)


def round_movies():
    '''
    循环获取url,top250
    '''
    n = 10
    count = 0
    for i in range(n):
        log('page', count)
        url = 'https://movie.douban.com/top250/?start={}'.format(count)
        movies = movies_from_url(url)
        # 打印每页第一个
        log('movies', movies[0])
        # 打印全部
        # log('movies', movies)
        # download_covers(movies)
        count += 25


def main():
    # 豆瓣电影 top250
    round_movies()


if __name__ == '__main__':
    # test()
    main()


# 以下 test 开头的函数是单元测试
def test_parsed_url():
    """
   测试函数来运行看检测是否正确运行
    """
    http = 'http'
    https = 'https'
    host = 'g.cn'
    path = '/'
    test_items = [
        ('g.cn', (http, host, 80, path)),
        ('http://g.cn', (http, host, 80, path)),
        ('http://g.cn/', (http, host, 80, path)),
        ('http://g.cn:90', (http, host, 90, path)),
        ('http://g.cn:90/', (http, host, 90, path)),
        #
        ('https://g.cn', (https, host, 443, path)),
        ('https://g.cn:233/', (https, host, 233, path)),
    ]
    for t in test_items:
        url, expected = t
        u = parsed_url(url)
        # 如果断言成功, 条件成立, 则通过测试, 否则为测试失败, 中断程序报错
        e = "parsed_url ERROR, ({}) ({}) ({})".format(url, u, expected)
        assert u == expected, e


def test_parsed_response():
    """
    测试是否能正确解析响应
    """
    # NOTE, 行末的 \ 表示连接多行字符串
    response = 'HTTP/1.1 301 Moved Permanently\r\n' \
               'Content-Type: text/html\r\n' \
               'Location: https://movie.douban.com/top250\r\n' \
               'Content-Length: 178\r\n\r\n' \
               'test body'
    status_code, header, body = parsed_response(response)
    assert status_code == 301
    assert len(list(header.keys())) == 3
    assert body == 'test body'


def test_get():
    """
    测试是否能正确处理 HTTP 和 HTTPS
    """
    urls = [
        'http://movie.douban.com/top250',
        'https://movie.douban.com/top250',
    ]
    for u in urls:
        get(u)


def test():
    """
    用于测试的主函数
    """
    test_parsed_url()
    test_get()
    test_parsed_response()
