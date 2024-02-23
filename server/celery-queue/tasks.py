import os
import shutil
import time
import tempfile
import requests
import subprocess
import json
import glob
import time
from db import MetaDB
from functools import wraps

from celery import Celery
from planutils.package_installation import PACKAGES
from celery.exceptions import SoftTimeLimitExceeded

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_RESULT_EXPIRE=os.environ.get('CELERY_RESULT_EXPIRE', 86400)

WEB_DOCKER_URL = os.environ.get('WEB_DOCKER_URL', None)
TIME_LIMIT=int(os.environ.get('TIME_LIMIT', 20))
celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery.conf.update(result_extended=True)
# result_expires in seconds: https://docs.celeryq.dev/en/latest/userguide/configuration.html#result-expires
celery.conf.update(result_expires=CELERY_RESULT_EXPIRE)
meta_db=MetaDB()


def track_celery(method):
    """
    This decorator measures celery task meta data and store it in Mysql db.

    Usage:
    Decorate your functions like this:
    @track_celery
    def my_long_running_and_mem_consuming_function():
        ...
    """
    @wraps(method)
    def measure_task(*args, **kwargs):
        start_time_of_task = time.time()
        result,arguments = method(*args, **kwargs)
        end_time_of_task = time.time()
        end_time_of_task - start_time_of_task
        duration=(end_time_of_task - start_time_of_task)
        # Update the meta_data table, args[0] is the celery task object(self)
        meta_db.add_meta_basic(args[0].request.id,"tasks.run.package",duration)
        meta_db.add_meta_advanced(args[0].request.id,bytes(json.dumps(result), 'utf-8'))
        return result,arguments

    return measure_task


def download_file( url: str, dst: str):
    r = requests.get(url)
    with open(dst, 'wb') as f:
        f.write(r.content)

def retrieve_output_file(target_file:dict, folder):
    file_pattern=os.path.join(folder, target_file["files"])
    file_list=glob.glob(file_pattern)
    output={}
    for file in file_list:
        file_name=os.path.basename(file)
        with open(file, 'r') as f:
            file_content = f.read()
            if target_file['type'] == 'json':
                file_content = json.loads(file_content)
        output[file_name]=file_content
    return output

def write_to_temp_file(name:str, data:str, folder:str):
    path = os.path.join(folder, name)
    with open(path, 'w') as f:
        f.write(data)
    return path

# The solve endpoint is replaced by the runpackage completely? So I have commented the following code.
# # Solve using downloaded flask files - not strings
# @celery.task(name='tasks.solve')
# def solve(domain_url: str, problem_url: str, solver: str) -> str:
#     tmpfolder = tempfile.mkdtemp()

#     if WEB_DOCKER_URL != None:
#         domain_url = domain_url.replace("localhost", WEB_DOCKER_URL)
#         problem_url = problem_url.replace("localhost", WEB_DOCKER_URL)

#     domain_file = f'{tmpfolder}/{os.path.basename(domain_url)}'
#     download_file(domain_url, domain_file)

#     problem_file = f'{tmpfolder}/{os.path.basename(problem_url)}'
#     download_file(problem_url, problem_file)

#     # Will generate a single output file (the plan) which is returned via HTTP
#     command = f"{solver} {domain_file} {problem_file}"
#     res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
#                         executable='/bin/bash', encoding='utf-8',
#                         shell=True, cwd=tmpfolder)

#     # remove the tmp/fies once we finish
#     os.remove(domain_file)
#     os.remove(problem_file)

#     plan = retrieve_output_file(PACKAGES[solver]['endpoint']['services']['solve']['return']['file'], tmpfolder)

#     shutil.rmtree(tmpfolder)

#     return {'stdout': res.stdout, 'stderr': res.stderr, 'plan':plan}

# Running generic planutils packages with no solver-specific assumptions

@celery.task(name='tasks.run.package',soft_time_limit=TIME_LIMIT+10,bind=True)
@track_celery
def run_package(self, package: str, arguments:dict, call:str, output_file:dict,**kwargs):


    try:
        tmpfolder = tempfile.mkdtemp()
        # Write files and replace args in the call string
        for k, v in arguments.items():
            if v['type'] == 'file':
                # Need to write to a temp file
                path_to_file = write_to_temp_file(k, v['value'], tmpfolder)
                # k is a file, we want to replace with the file path
                call = call.replace("{%s}" % k, k)
            else:
                # k needs to be replaced with the value
                call = call.replace("{%s}" % k, str(v['value']))

        
        # Avoid planutils consuming a planner argument
        planner = call.split(' ')[0]
        args = ' '.join(call.split(' ')[1:])
        call = f'{planner} -- {args}'
        call = f"timeout {TIME_LIMIT} planutils run {call}"
        
        res = subprocess.run(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            executable='/bin/bash', encoding='utf-8',
                            shell=True, cwd=tmpfolder)

        output = retrieve_output_file(output_file, tmpfolder)
        # Remove the files in temfolder when task is finished
        shutil.rmtree(tmpfolder)
        result={"stdout":res.stdout, "stderr":res.stderr, "call":call, "output":output,"output_type":output_file["type"]}
        return result,arguments
    except SoftTimeLimitExceeded as e:
        return {"stdout":"Request Time Out", "stderr":"", "call":call, "output":{},"output_type":output_file["type"]},arguments
