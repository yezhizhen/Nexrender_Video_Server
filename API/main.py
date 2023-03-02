from http.server import BaseHTTPRequestHandler #,ThreadingHTTPServer
import socketserver
import argparse
import base64
import json
from constants.my_constants import *
from video_generation import generate_video_from_string
import requests

PORT = 80


#server to handle POST of csv and json
class ServerHandler(BaseHTTPRequestHandler):
    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Test"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def invalid_IP(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Your IP not allowed')

    def do_POST(self):
        if self.client_address[0] not in allowed_ips:
            print(f"Invalid IP from {self.client_address[0]}")
            self.invalid_IP()
        elif self.headers.get('Authorization') == None:
            self.do_AUTHHEAD()
            self.wfile.write(b'no auth header received')
        elif self.headers.get('Authorization') == 'Basic '+self.auth:
            print(f"Success auth from {self.client_address[0]}")              
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            post_data = json.loads(post_data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            file_name = post_data["json_file"]["actions"]["postrender"][0]["output"]
            post_data["json_file"]["actions"]["postrender"][1]["output"] = OUTPUT_DIR + file_name
            
            body = {"filename":file_name}
            response_data = json.dumps(body).encode()
            self.wfile.write(response_data)

            #print(post_data["csv_file"])
            #trigger a vid gen task
            generate_video_from_string(post_data["json_file"], post_data["csv_file"])

            #send video after gen
            requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params = body)

            
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
    parser.add_argument('-p', '--port', type=int, default=PORT, help='port to listen on')
    parser.add_argument('-u', '--user', type=str, default=USERNAME, help='username')
    parser.add_argument('-w', '--password', type=str, default=PASSWORD, help='password')
    args = parser.parse_args()


    # Create auth string
    auth = base64.b64encode(bytes(args.user+':'+args.password, 'utf-8')).decode('ascii')

    # Create server
    handler = ServerHandler
    handler.auth = auth
    #
    #httpd = ThreadingHTTPServer(("", args.port), handler)
    httpd = socketserver.TCPServer(("", args.port), handler)
    # Start server
    print('Serving at port', args.port)
    httpd.serve_forever()
    

if __name__ == '__main__':
    main()


