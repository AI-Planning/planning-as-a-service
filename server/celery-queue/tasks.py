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
    
    # if utility['solver']:
    # We have a solver, expect the form <exe> <domain> <problem>
    # Will generate a single output file (the plan) which is returned via HTTP
    command = f"{solver} {domain_file} {problem_file}"
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        executable='/bin/bash', encoding='utf-8',
                        shell=True, cwd=tmpfolder)

    # remove the tmp/fies once we finish
    os.remove( domain_file )
    os.remove( problem_file )
    files = os.listdir(tmpfolder)

    plans = {}

    for file in files:
        fpath = f'{tmpfolder}/{file}'
        f = open(fpath, "r")
        plans[file] = f.readlines()

    shutil.rmtree(tmpfolder)

    return {'stdout': res.stdout, 'stderr': res.stderr, 'plans':plans}\
        

@celery.task(name='tasks.solve.string')
def solve(domain: [str], problem: [str], solver: str) -> str:

    tmpfolder = tempfile.mkdtemp()

    # Want to write these strings to tmp files in tmpfolder
    domain_path = os.path.join(tmpfolder, "domain.pddl")
    domain_file = open(domain_path, "w")
    domain_file.writelines(domain)
    domain_file.close()
    
    problem_path = os.path.join(tmpfolder, "problem.pddl")
    problem_file = open(problem_path, "w")
    problem_file.writelines(problem)
    problem_file.close()

    # PACKAGES[solver] contains package manifest information 

    command = f"{solver} {domain_path} {problem_path}"
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        executable='/bin/bash', encoding='utf-8',
                        shell=True, cwd=tmpfolder)

    # # remove the tmp/fies once we finish
    os.remove( domain_path )
    os.remove( problem_path )
    files = os.listdir(tmpfolder)

    plans = {}

    for file in files:
        fpath = f'{tmpfolder}/{file}'
        f = open(fpath, "r")
        plans[file] = f.readlines()

    shutil.rmtree(tmpfolder)

    return {'stdout': res.stdout, 'stderr': res.stderr, 'plans':plans}

@celery.task(name='tasks.add')
def add(x: int, y: int) -> int:
    time.sleep(5)
    return x + y
