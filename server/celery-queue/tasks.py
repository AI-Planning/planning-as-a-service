import os
import shutil
import time
import tempfile
import requests
import subprocess
import json

from celery import Celery
from planutils.package_installation import PACKAGES


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
WEB_DOCKER_URL = os.environ.get('WEB_DOCKER_URL', None)

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

def download_file( url: str, dst: str):
    r = requests.get(url)
    with open(dst, 'wb') as f:
        f.write(r.content)
        
def retrieve_output_file(target_file:str, folder):
    available_files = os.listdir(folder)
    output = {}
    for file in available_files:
        if file == target_file['file']:
            fpath = f'{folder}/{file}'
            f = open(fpath, "r")
            if target_file['type'] == 'json':
                output[file] = json.loads(f.read())
            else:
                output[file] = f.read()
            break
    return output

def write_to_temp_file(name:str, data:str, folder:str):
    path = os.path.join(folder, name)
    file = open(path, "w")
    file.write(data)
    file.close()
    return path

# Solve using downloaded flask files - not strings
@celery.task(name='tasks.solve')
def solve(domain_url: str, problem_url: str, solver: str) -> str:
    tmpfolder = tempfile.mkdtemp()

    if WEB_DOCKER_URL != None:
        domain_url = domain_url.replace("localhost", WEB_DOCKER_URL)
        problem_url = problem_url.replace("localhost", WEB_DOCKER_URL)

    domain_file = f'{tmpfolder}/{os.path.basename(domain_url)}'
    download_file(domain_url, domain_file)

    problem_file = f'{tmpfolder}/{os.path.basename(problem_url)}'
    download_file(problem_url, problem_file)
    
    # Will generate a single output file (the plan) which is returned via HTTP
    command = f"{solver} {domain_file} {problem_file}"
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        executable='/bin/bash', encoding='utf-8',
                        shell=True, cwd=tmpfolder)

    # remove the tmp/fies once we finish
    os.remove(domain_file)
    os.remove(problem_file)
    
    plans = retrieve_output_files(PACKAGES[solver]['endpoint']['return']['file'], tmpfolder)
    
    shutil.rmtree(tmpfolder)

    return {'stdout': res.stdout, 'stderr': res.stderr, 'plans':plans}

# Running generic planutils packages with no solver-specific assumptions
@celery.task(name='tasks.run.package')
def run_package(package: str, arguments:dict, call:str, output_file:str):
    tmpfolder = tempfile.mkdtemp()
    
    # Write files 
    for k, v in arguments.items():
        if v['type'] == 'file':
            # Need to write to a temp file
            path_to_file = write_to_temp_file(k, v['value'], tmpfolder)
            # k is a file, we want to replace with the file path
            call = call.replace("{%s}" % k, k)
        else:
            # k needs to be replaced with the value 
            call = call.replace("{%s}" % k, str(v['value']))

    # Run the command
    res = subprocess.run(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        executable='/bin/bash', encoding='utf-8',
                        shell=True, cwd=tmpfolder)
    
    output = retrieve_output_file(output_file, tmpfolder)

    return {"Stdout":res.stdout, "Stderr":res.stderr, "call":call, "output":output}
    
    
        

@celery.task(name='tasks.solve.string')
def solve(domain: str, problem: str, solver: str) -> str:
    
    tmpfolder = tempfile.mkdtemp()

    domain_path = write_to_temp_file("domain.pddl", domain, tmpfolder)
    problem_path = write_to_temp_file("problem.pddl", problem, tmpfolder)

    command = f"{solver} {domain_path} {problem_path}"
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        executable='/bin/bash', encoding='utf-8',
                        shell=True, cwd=tmpfolder)

    # # remove the tmp/fies once we finish
    os.remove(domain_path)
    os.remove(problem_path)
    plans = retrieve_output_files(PACKAGES[solver]['endpoint']['return']['file'], tmpfolder)
    shutil.rmtree(tmpfolder)

    return {'stdout': res.stdout, 'stderr': res.stderr, 'plans':plans}
