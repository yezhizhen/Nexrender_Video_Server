import subprocess
from constants.my_constants import *
import re
from json import dumps
#import uuid

def generate_video(json_path):
    print(f"Generating video with JSON in {json_path}")
    subprocess.run([NEXRENDER_PATH,"--file",json_path])


def extract_template_no(input, exp = r'-Template-(\d+)_'):
    pattern = re.compile(exp)
    result = pattern.search(input)
    return result.groups()[0]

def generate_video_from_string(json, csv):
    template_no = extract_template_no(json["template"]["composition"])
    json_path = TEMP_JSON_PATH.format(template_no,"temp.json")
    csv_path = TEMP_CSV_PATH.format(template_no)
    #write json to file
    with open(json_path,"w") as f:
        f.write(dumps(json))

    with open(csv_path,"w") as f:
        f.write(csv)

    generate_video(json_path)
    