import os
import time
import tempfile
import requests

from celery import Celery

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
    
    tmpfolder = tempfile.gettempdir()
    
    if WEB_DOCKER_URL != None:
        domain_url = domain_url.replace("localhost", WEB_DOCKER_URL)
        problem_url = problem_url.replace("localhost", WEB_DOCKER_URL)

    domain_file = f'{tmpfolder}/{os.path.basename(domain_url)}'
    download_file(domain_url, domain_file)    
    
    problem_file = f'{tmpfolder}/{os.path.basename(problem_url)}'
    download_file(problem_url, problem_file)
    
    #TODO: Run planner using plan-utils


    # remove the tmp/fies once we finish
    os.remove( domain_file )
    os.remove( problem_file )

    return f"no solution found using {domain_file} and {problem_file} using {solver}"


    

@celery.task(name='tasks.add')
def add(x: int, y: int) -> int:
    time.sleep(5)
    return x + y
