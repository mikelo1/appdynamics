#!/usr/bin/python
import yaml
import subprocess
import sys

auth_file="auth_file.csv"

def read_jobs_yaml(jobsfile):
    try:
        stream = open(jobsfile)
    except IOError:
        create_new_config_yaml()

    with open(jobsfile, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

if len(sys.argv) < 2:
    print("Syntax: run_jobs.py <job_file.yaml>")
    exit()

jobs = read_jobs_yaml(sys.argv[1])

for job in jobs['jobs']:
    command = job['command']
    url     = job['url']
    username= job['apiclient']
    entities=','.join(map(lambda x: str(x),job['entities']))
    
    subprocess.call("./appdctl.py login --controller-url "+url+" --api-client "+username+" --basic-auth-file "+auth_file, shell=True)
    subprocess.call("./appdctl.py "+command+" -a "+entities, shell=True)
    #print command,url,username,entities