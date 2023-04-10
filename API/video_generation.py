import subprocess
from constants.my_constants import *
import re
from json import dumps
import time
import sys
#import uuid

def generate_video(json_path):

    print(f"Generating video with JSON in {json_path}")
    
    '''
    redirect stderr to PIPE object, and read in the end.
    p = subprocess.Popen([NEXRENDER_PATH,"--file",json_path], stderr=subprocess.PIPE)
    error_msg = p.stderr.read().decode()
    '''
    """
    mute the stdout. Capture stderr.
    p = subprocess.Popen([NEXRENDER_PATH,"--file",json_path], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
    """

    p = subprocess.Popen([NEXRENDER_PATH,"--file",json_path, "--ae", "reuse"], stderr=sys.stdout, stdout=subprocess.PIPE)
    
    #capture stdout until rendering finished.
    #only print stdout for every 10%
    for line in p.stdout: #this would keep the new line character in line
        
        progress = re.search("rendering progress (\d+)%", line.decode())
        if progress is not None:
            percent = progress.group(1)
            if int(percent) % 20 == 0:
                print(line.decode())
        else:
            res = re.findall("rendering took ~\d+\.\d+ sec", line.decode())
            if len(res) > 0:
                print(res[0])
                #without close, wait would cause deadlock
                p.stdout.close()
                break
    #rendering finished. Waiting for encoding.
    print("Encoding..")
    start = time.time()
    p.wait()
    print(f"Encoding took: {time.time() - start:.2f} sec")

    #os.kill(p.pid, signal.SIGINT)
        


def extract_template_no(input, exp = r'-Template-(\d+)_'):
    #pattern = re.compile(exp)
    #result = pattern.search(input)
    result = re.search(exp,input)
    return result.groups()[0]

#infer the template number and generate
#json here is json object
def generate_video_from_string(json, csv):
    template_no = extract_template_no(json["template"]["composition"])
    json_path = TEMP_JSON_PATH.format(template_no)
    csv_path = TEMP_CSV_PATH.format(template_no)
    #write json to file
    with open(json_path,"w") as f:
        f.write(dumps(json))

    with open(csv_path,"w") as f:
        f.write(csv)

    generate_video(json_path)
    return template_no