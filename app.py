import socket
import urllib.parse

from routes.routes_user import route_dict as user_routes
from routes.routes_todo import route_dict as todo_routes

from utils import log
from utils import route_static


class Request(object):
    def __init__(self):
        self.method = 'GET'
        self.path = ''
        self.query = {}
        self.body = ''
        self.headers = {}
        self.cookies = {}

    def add_cookies(self):
        cookies = self.headers.get('Cookie', '')
        kvs = cookies.split('; ')
        log('cookie', kvs)
        for kv in kvs:
            if '=' in kv:
                k, v = kv.split('=')
                self.cookies[k] = v

    def add_headers(self, header):
        lines = header
        for line in lines:
            k, v = line.split(': ', 1)
            self.headers[k] = v
        self.add_cookies()

    def form(self):
        body = urllib.parse.unquote(self.body)
        args = body.split('&')
        f = {}
        log('form debug', args, len(args))
        for arg in args:
            k, v = arg.split('=')
            f[k] = v
        return f


request = Request()


def error(request, code=404):
    e = {
        404: b'HTTP/1.1 404 NOT FOUND\r\n\r\n<h1>NOT FOUND</h1>',
    }
    return e.get(code, b'')


def parsed_path(path):
    index = path.find('?')
    if index == -1:
        return path, {}
    else:
        path, query_string = path.split('?', 1)
        args = query_string.split('&')
        query = {}
        for arg in args:
            k, v = arg.split('=')
            query[k] = v
        return path, query


def register_routes(base_routes, routes, prefix=''):
    if prefix != '':
        routes = {prefix + k: v for k, v in routes.items()}
    base_routes.update(routes)


def response_for_path(path):
    path, query = parsed_path(path)
    request.path = path
    request.query = query
    log('path and query', path, query)
    r = {
        '/static': route_static,
    }
    # 注册外部的路由
    r.update(user_routes)
    r.update(todo_routes)
    response = r.get(path, error)
    return response(request)


def run(host='', port=3000):
    import routes.session
    routes.session.load_session()
    log('start at', '{}:{}'.format(host, port))
    with socket.socket() as s:
        s.bind((host, port))
        # 无限循环来处理请求
        while True:
            # 监听 接受 读取请求数据 解码成字符串
            s.listen(3)
            connection, address = s.accept()
            r = connection.recv(1100)
            r = r.decode('utf-8')
            log('完整请求')
            log(r.replace('\r\n', '\n'))
            log('请求结束')
            if len(r.split()) < 2:
                continue
            path = r.split()[1]
            request.method = r.split()[0]
            request.add_headers(r.split('\r\n\r\n', 1)[0].split('\r\n')[1:])
            request.body = r.split('\r\n\r\n', 1)[1]
            response = response_for_path(path)
            log(response)
            connection.sendall(response)
            # log('完整响应')
            # log(response.decode('utf-8'))
            # log('响应结束')
            # 处理完请求, 关闭连接
            connection.close()


if __name__ == '__main__':
    config = dict(
        host='',
        port=3000,
    )
    run(**config)
