import os
import time
from celery import Celery


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379')

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@celery.task(name='tasks.solve')
def solve(domain: str, problem: str) -> str:
    
    #TODO: Run planner using plan-utils

    return f"no solution found using {domain} and {problem}"


    

@celery.task(name='tasks.add')
def add(x: int, y: int) -> int:
    time.sleep(5)
    return x + y
