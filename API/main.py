from http.server import BaseHTTPRequestHandler #,ThreadingHTTPServer
import socketserver
import argparse
import base64
import threading
import json
from constants.my_constants import *
from video_generation import generate_video_from_string
import requests
from datetime import datetime
import pytz
import pysftp
#remove following line if SSL certificate is ready
#import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORT = 80


#server to handle POST of csv and json
"""
JSON received 
[{"json_file":"...","csv_file":"..."},{"json_file":"...","csv_file":"..."},{"json_file":"...","csv_file":"..."}]
"""
mutex = threading.Lock()

def background_generation_task(post_data):
    mutex.acquire()
    try:
        for single_request in post_data:
            file_name = single_request["json_file"]["actions"]["postrender"][0]["output"]
            single_request["json_file"]["actions"]["postrender"][1]["output"] = OUTPUT_DIR + file_name
            #print(single_request["csv_file"])
            #trigger a vid gen task
            print("Genearting " + file_name)
            template_no = generate_video_from_string(single_request["json_file"], single_request["csv_file"])
            #SFTP the file
            
            with pysftp.Connection(SFTP_HOST, username=SFTP_USERNAME, private_key= PRIVATE_KEY_PATH) as sftp:
                sftp.put(OUTPUT_DIR + file_name, SFTP_DEST.format(template_no) + file_name)

            print(f'Upload done for {file_name}.')

            #confirm completion of video transferring
            #Comment after certificate ready

            #requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params ={"filename":file_name}, verify=False)
            requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params ={"filename":file_name}, verify=CONFIRM_API_CERT_PATH)
        print(f"All Completed at {datetime.now(tz=pytz.timezone('Asia/Hong_Kong'))}.")
    finally:
        mutex.release()



class ServerHandler(BaseHTTPRequestHandler):
    
    def generation_handler(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        post_data = json.loads(post_data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        body = {"status": "Success"}
        response_data = json.dumps(body).encode()
        self.wfile.write(response_data)
        #start a thread
        t = threading.Thread(target=background_generation_task, args=(post_data,), daemon=True)
        t.start()    

    def compression_handler(self):
        pass

    ROUTES_to_handler = {'/':generation_handler,'/news_compression':compression_handler}    
    ROUTES = ROUTES_to_handler.keys()          

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Test"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def invalid_IP(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Your IP not allowed')

    #only handle request at path /
    def do_POST(self):
        if self.path not in ServerHandler.ROUTES:
            print("Posting wrong address.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Not accessible.')  

        elif self.address_string() not in allowed_ips:
            print(f"Invalid IP from {self.address_string()}")
            self.invalid_IP()
        elif self.headers.get('Authorization') == None:
            self.do_AUTHHEAD()
            self.wfile.write(b'no auth header received')
        elif self.headers.get('Authorization') == 'Basic '+self.auth:
            print(f"Success auth from {self.client_address[0]}")              
            ServerHandler.ROUTES_to_handler[self.path](self)

        else:
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.get('Authorization').encode('utf-8'))
            self.wfile.write(b'not authenticated')
    
    '''
    def log_message(self, format, *args):
        """
        Disable logging.
        """
        return
    '''
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


