from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
from datetime import datetime
import json
import os
from jinja2 import Environment, FileSystemLoader

DATA_FILE = 'storage/data.json'

class DataHandler:
    def __init__(self, filepath):
        self.filepath = filepath

    def save_data(self, data):
        curr_data = self.load_data()
        curr_data.update(data)
        with open(self.filepath, 'w') as file:
            json.dump(curr_data, file)

    def load_data(self):
        if not os.path.exists(self.filepath) or os.stat(self.filepath).st_size == 0:
            return {}
        
        with open(self.filepath, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {} 

class HtmlTemplate:
    def __init__(self, template_path):
        self.env = Environment(loader=FileSystemLoader("."))
        self.template = self.env.get_template(template_path)

    def render(self, **kwargs):
        output = self.template.render(
            **kwargs,
        )
        return output.encode("utf-8")

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        elif pr_url.path == '/read':
            self.send_template('read.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_template(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        data = DataHandler(DATA_FILE).load_data()

        template = HtmlTemplate(filename)
        self.wfile.write(template.render(data=data))

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}

        DataHandler(DATA_FILE).save_data({str(datetime.now()): data_dict})

        self.send_response(302)
        self.send_header('Location', '/read')
        self.end_headers()


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

if __name__ == '__main__':
    run()
