import subprocess
from constants.my_constants import *
import re
from json import dumps
import time
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

    p = subprocess.Popen([NEXRENDER_PATH,"--file",json_path], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    
    #capture stdout until rendering finished.
    while p.poll() is None:
        time.sleep(3)
        new_stdout_msg = p.stdout.read().decode()
        res = re.findall("rendering took ~\d+\.\d+ sec", new_stdout_msg)
        if len(res) > 0:
            print(res[0])
            break
    #rendering finished. Waiting for encoding.
    start = time.time()
    p.wait()
    error_msg = p.stderr.read().decode()
    if len(error_msg) > 0:
        print("Error encountred." ,error_msg, sep="\n")
    print(f"Encoding took: {time.time() - start:.2f} sec")

    #os.kill(p.pid, signal.SIGINT)
        


def extract_template_no(input, exp = r'-Template-(\d+)_'):
    #pattern = re.compile(exp)
    #result = pattern.search(input)
    result = re.search(exp,input)
    return result.groups()[0]

def generate_video_from_string(json, csv):
    template_no = extract_template_no(json["template"]["composition"])
    json_path = TEMP_JSON_PATH.format(template_no,"temporary")
    csv_path = TEMP_CSV_PATH.format(template_no)
    #write json to file
    with open(json_path,"w") as f:
        f.write(dumps(json))

    with open(csv_path,"w") as f:
        f.write(csv)

    generate_video(json_path)
    return template_no
    