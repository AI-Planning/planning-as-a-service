import os
import shutil
import time
import tempfile
import requests
import subprocess

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
        
def retrieve_output_files(target_files: [str], folder):
    available_files = os.listdir(folder)
    output = {}
    for file in available_files:
        if file in target_files:
            fpath = f'{folder}/{file}'
            f = open(fpath, "r")
            output[file] = f.readlines()
    return output

def write_to_temp_file(name:str, data:str, folder:str):
    path = os.path.join(folder, name)
    file = open(path, "w")
    file.write(data)
    file.close()

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
def run_package(package: str, arguments:dict, call, output_files:[str]):
    # Write all file type arguments to a created temp folder in which we can run the service
    # Call should remain unchanged, and we should write files with the same names as the call string has - 
        # Leave it up to the manifest to make sure that they match
    tmpfolder = tempfile.mkdtemp()
    # Write files 
    for name, value in arguments.items():
        if value['type'] == 'file':
            # Need to write to a temp file
            write_to_temp_file(name, value['value'], tmpfolder)
    # Run the command
    res = subprocess.run(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        executable='/bin/bash', encoding='utf-8',
                        shell=True, cwd=tmpfolder)
    
    output = retrieve_output_files(output_files, tmpfolder)
    
    return {"Stdout":res.stdout, "Stderr":res.stderr, "Result":output}
    
    
        

@celery.task(name='tasks.solve.string')
def solve(domain: str, problem: str, solver: str) -> str:
    
    tmpfolder = tempfile.mkdtemp()

    write_to_temp_file("domain.pddl", domain, tmpfolder)
    write_to_temp_file("problem.pddl", problem, tmpfolder)

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
