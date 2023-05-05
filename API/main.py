from http.server import BaseHTTPRequestHandler #,ThreadingHTTPServer
import socketserver
import argparse
import base64
import threading
import json
from constants.my_constants import *
from video_generation import generate_video_from_string, generate_video
import requests
from datetime import datetime
import pytz
import pysftp
import shutil
import time
#remove following line if SSL certificate is ready
#import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORT = 80


#server to handle POST of csv and json
"""
JSON received 
[{"json_file":"...","csv_file":"..."},{"json_file":"...","csv_file":"..."},{"json_file":"...","csv_file":"..."}]
"""
mutex = threading.Lock()

def print_t(msg):
    print(msg + f". At {time_now()}")

def time_now():
    return (datetime.now(tz=pytz.timezone('Asia/Hong_Kong')))

def background_generation_task(post_data):
    mutex.acquire()
    cnt = 0
    
    print(f"Generating {len(post_data)} videos...")
    for single_request in post_data:
        failed_before = False
        while True:
            try:
                if not failed_before:
                    output_name = single_request["json_file"]["actions"]["postrender"][0]["output"]
                    single_request["json_file"]["actions"]["postrender"][1]["output"] = OUTPUT_DIR + output_name
                    #print(single_request["csv_file"])
                    #trigger a vid gen task
                    print_t("Genearting " + output_name)
                    template_no = generate_video_from_string(single_request["json_file"], single_request["csv_file"])
                else:
                    print_t("Genearting " + output_name)
                    generate_video(TEMP_JSON_PATH.format(template_no))
                #SFTP the file  
                with pysftp.Connection(SFTP_HOST, username=SFTP_USERNAME, private_key= PRIVATE_KEY_PATH) as sftp:
                    sftp.put(OUTPUT_DIR + output_name, SFTP_DEST.format(template_no) + output_name)
                print_t(f'Upload done for {output_name}.')
                #confirm completion of video transferring
                #Comment after certificate ready
                requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params ={"filename":output_name}, verify=False)
                #requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params ={"filename":output_name}, verify=CONFIRM_API_CERT_PATH)
                cnt += 1
                print(f"{len(post_data) - cnt} tasks remaining for the current task\n")
                break
            except FileNotFoundError as e:
                print(e)
                if not failed_before:
                #log the .csv and .json with error
                    shutil.copy2(TEMP_JSON_PATH.format(template_no), ERROR_LOGS_PATH + output_name + '.json')
                    shutil.copy2(TEMP_CSV_PATH.format(template_no), ERROR_LOGS_PATH + output_name + '.csv')
                
                time.sleep(5)
                #probably try rerun the program
                print("Rerunning with the same files..")
                
                failed_before = True


    print(f"All Completed at {time_now()}.") 
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
        print(f"Post request at {time_now()}.") 
        if self.path not in ServerHandler.ROUTES:
            print(f"Posting wrong address {self.path} from {self.address_string()}.")
            self.send_response(400)
            self.end_headers()
            #self.wfile.write(b'Not accessible.')  

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


