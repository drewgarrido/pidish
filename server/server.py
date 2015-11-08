import time
import BaseHTTPServer
import cgi

import inspect
import view
from model import model


HOST_NAME = ''   # Normally a domain name. Blank still allows IP address URL
PORT_NUMBER = 80 # TCP port

SYNC_MODEL = None
VIEWS = {}

def parse_url_args(args):
    parsing = {}
    data = args.split('&')
    for couple in data:
        name, value = couple.split('=')
        parsing[name]=value
    return parsing


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""

        if self.path[0] == '/':
            self.path = self.path[1:]
        if self.path == '':
            self.path = 'index'

        if self.path in VIEWS:
            page = VIEWS[self.path]()

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(page)
        else:
            self.send_error(404)



    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = parse_url_args(self.rfile.read(length))
        else:
            postvars = {}

        SYNC_MODEL.send_command(postvars)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(view.index())

if __name__ == '__main__':
    global SYNC_MODEL

    items = inspect.getmembers(view,predicate=inspect.isfunction)
    for item in items:
        VIEWS[item[0]]=item[1]

    VIEWS.pop('load',None)

    SYNC_MODEL = model()
    SYNC_MODEL.start()

    # Initialize the view
    view.load(SYNC_MODEL)

    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

    SYNC_MODEL.shutdown()
    SYNC_MODEL.join()
