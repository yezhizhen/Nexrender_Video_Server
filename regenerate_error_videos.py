
from API.video_generation import generate_video_from_string, generate_video, extract_template_no
from constants.my_constants import *
import requests
from datetime import datetime
import pytz
import pysftp
import shutil
import os
import pathlib
import re


def extract_template_no_from_file_name(str):
    result = re.search('RFT(\d+)',str)
    return result.groups()[0]

#dir should contain '/' in the end
def generate_all_in_folder(dir = 'error_log/'):
    print(f"Starting on {datetime.now(tz=pytz.timezone('Asia/Hong_Kong'))}.") 
    cnt = 0
    files = os.listdir(dir)
    vid_total = int(len(files)/2)
    print(f"Generating {vid_total} videos...")
    for file in files:
        failed_before = False
        if pathlib.Path(file).suffix != '.json':
            continue
        #file must be '.json'
        #retry this path if fails
        template_no = extract_template_no_from_file_name(file)
        output_name = file[:-len('.json')]
        
        while True:
            try:
                if not failed_before:
                    #trigger a vid gen task
                    print("Genearting " + output_name)
                    #move file to 
                    shutil.copy2(dir + file, TEMP_JSON_PATH.format(template_no))
                    shutil.copy2(dir + output_name + '.csv', TEMP_CSV_PATH.format(template_no))
                generate_video(TEMP_JSON_PATH.format(template_no))
                #SFTP the file  
                with pysftp.Connection(SFTP_HOST, username=SFTP_USERNAME, private_key= PRIVATE_KEY_PATH) as sftp:
                    sftp.put(OUTPUT_DIR + output_name, SFTP_DEST.format(template_no) + output_name)
                print(f'Upload done for {output_name}.')
                #confirm completion of video transferring
                #Comment after certificate ready
                #requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params ={"filename":output_name}, verify=False)
                requests.get(DOWNLOAD_INITIATOR_ENDPOINT, params ={"filename":output_name}, verify=CONFIRM_API_CERT_PATH)
                cnt += 1
                print(f"{vid_total - cnt} tasks remaining for the current task\n")
                break
            except Exception as e:
                print(e)
                import time
                time.sleep(1)
                #probably try rerun the program
                print("Rerunning with the same files..")
                failed_before = True


    print(f"All Completed at {datetime.now(tz=pytz.timezone('Asia/Hong_Kong'))}.") 

if __name__ == '__main__':
    generate_all_in_folder()