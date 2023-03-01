"""
Create a https server with authentication that serves files. Disable logging.
"""

import os
import argparse
import socketserver
import base64

from http.server import SimpleHTTPRequestHandler
from constants.my_constants import *

class AuthHandler(SimpleHTTPRequestHandler):
    """
    Simple HTTP request handler with authentication.
    """
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Test"')
        #self.send_header('Content-type', 'text/html')
        self.end_headers()

    def invalid_IP(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Your IP not allowed')

    def do_GET(self):
        """Serve a GET request."""
        print(self.client_address[0])
        
        
        if self.client_address[0] not in allowed_ips:
            self.invalid_IP()
        elif self.headers.get('Authorization') == None:
            self.do_AUTHHEAD()
            self.wfile.write(b'no auth header received')
        elif self.headers.get('Authorization') == 'Basic '+self.auth:
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.get('Authorization').encode('utf-8'))
            self.wfile.write(b'not authenticated')

    def log_message(self, format, *args):
        """
        Disable logging.
        """
        return

def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description='Simple http server with authentication.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='port to listen on')
    parser.add_argument('-d', '--dir', type=str, default='../Output_Videos', help='directory to serve')
    parser.add_argument('-u', '--user', type=str, default=USERNAME, help='username')
    parser.add_argument('-w', '--password', type=str, default=PASSWORD, help='password')
    args = parser.parse_args()

    # Change directory
    os.chdir(args.dir)

    # Create auth string
    auth = base64.b64encode(bytes(args.user+':'+args.password, 'utf-8')).decode('ascii')

    # Create server
    handler = AuthHandler
    handler.auth = auth
    httpd = socketserver.TCPServer(("", args.port), handler)

    # Start server
    print('Serving at port', args.port)
    httpd.serve_forever()

if __name__ == '__main__':
    main()