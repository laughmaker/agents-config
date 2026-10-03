#!/usr/bin/env python3
"""naval-study 本地静态服务器（支持 HTTP Range）。

为什么不用 python3 -m http.server：
    标准库的 SimpleHTTPRequestHandler 不实现 Range 请求。对本目录里
    286 MB 的 media/video.mp4 来说，后果是——每次点击句子跳转，浏览器
    都得把整个文件重新拉一遍，拖动进度条基本不可用。

用法：
    python3 serve.py            # 默认 http://127.0.0.1:8777/
    python3 serve.py 8080       # 换端口

排查跳转流量（会打印每个 Range 请求）：
    NAVAL_LOG_MEDIA=1 python3 serve.py

只监听 127.0.0.1，不对外暴露。
"""

import os
import re
import sys
import functools
import http.server
import socketserver

ROOT = os.path.dirname(os.path.abspath(__file__))
CHUNK = 256 * 1024
# 单次 Range 响应最多回多少字节。浏览器拖动进度条时常常直接请求
# 「从 N 到文件末尾」，若不封顶，服务器会开始传几百 MB，直到浏览器取够
# 了主动断开。封顶后每次只回一小段，浏览器按需续请求——拖动更跟手，
# 也不会产生大量被掐断的连接。
MAX_RANGE = 16 * 1024 * 1024
# NAVAL_LOG_MEDIA=1 时打印每个媒体请求（含 Range 头）
LOG_MEDIA = os.environ.get('NAVAL_LOG_MEDIA') == '1'
MEDIA_RE = re.compile(r'\.(mp4|m4a|webm|mp3|wav|ogg|mov|mkv)(\?|$)')


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    # HTTP/1.1 才有正确的 206 语义与连接复用
    protocol_version = 'HTTP/1.1'
    server_version = 'naval-study/1.0'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # 让浏览器知道可以对媒体文件发 Range 请求（seek 的前提）
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or os.path.isdir(path) or not os.path.isfile(path):
            return super().send_head()

        m = re.match(r'bytes=(\d*)-(\d*)\s*$', rng.strip())
        if not m:
            return super().send_head()

        size = os.path.getsize(path)
        first, last = m.group(1), m.group(2)
        if first == '' and last == '':
            return super().send_head()
        if first == '':                     # bytes=-N  取末尾 N 字节
            start = max(0, size - int(last))
            end = size - 1
        else:                               # bytes=N- / bytes=N-M
            start = int(first)
            end = int(last) if last else size - 1
            end = min(end, size - 1)
        # 即使客户端要「N 到末尾」，也只回一段，其余由它续请求
        end = min(end, start + MAX_RANGE - 1)

        if size == 0 or start >= size or start > end:
            self.send_response(416)
            self.send_header('Content-Range', 'bytes */%d' % size)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None

        f = open(path, 'rb')
        f.seek(start)
        self._range_left = end - start + 1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Content-Length', str(self._range_left))
        self.send_header('Last-Modified', self.date_time_string(os.path.getmtime(path)))
        self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        left = getattr(self, '_range_left', None)
        if left is None:
            return super().copyfile(source, outputfile)
        self._range_left = None
        while left > 0:
            chunk = source.read(min(CHUNK, left))
            if not chunk:
                break
            try:
                outputfile.write(chunk)
            except (ConnectionResetError, BrokenPipeError):
                return          # 浏览器取够了主动断开，属正常，不必报错
            left -= len(chunk)

    def log_request(self, code='-', size='-'):
        # 媒体文件会产生大量 Range 请求，默认静默；
        # NAVAL_LOG_MEDIA=1 时全部打印，可直观看到「跳到某处只取了多少字节」。
        rng = self.headers.get('Range') if self.headers else None
        msg = '%s %s → %s%s' % (self.command, self.path, code,
                                (' Range=%s' % rng) if rng else '')
        if not LOG_MEDIA and MEDIA_RE.search(self.path):
            return
        sys.stderr.write('%s - %s\n' % (self.address_string(), msg))

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            self.close_connection = True


class ReusableServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        # 长 Range 请求被浏览器中途掐断是常态，不要打堆栈吓人
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def main():
    port = 8777
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print('端口号必须是数字，例如：python3 serve.py 8080')
            return 1

    handler = functools.partial(RangeHandler)
    try:
        httpd = ReusableServer(('127.0.0.1', port), handler)
    except OSError as e:
        print('端口 %d 起不来：%s' % (port, e))
        print('可能已经有服务在跑，换一个端口试试：python3 serve.py %d' % (port + 1))
        return 1

    print('naval-study 已启动（支持 Range，拖动进度条可正常 seek）')
    print('  → http://127.0.0.1:%d/' % port)
    print('  按 Ctrl+C 停止')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')
    finally:
        httpd.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
