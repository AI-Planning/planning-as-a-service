import os
import shutil
import signal
import time
import tempfile
import requests
import subprocess
import json
import glob
import time
from types import SimpleNamespace
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
def run_package(self, package: str, arguments:dict, call:str, output_file:dict, max_time=None, **kwargs):

    time_limit = int(max_time) if max_time else TIME_LIMIT

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
        call = f"timeout {time_limit} planutils run {call}"
        
        # start_new_session=True makes this process (the shell running `call`)
        # its own process group leader. Its children (timeout, planutils, the
        # actual planner) inherit that same group by default, so killing the
        # whole group later (on cancellation) reliably takes all of them down
        # - killing just proc.pid would only kill the shell and orphan the
        # planner still running underneath it.
        proc = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            executable='/bin/bash', encoding='utf-8',
                            shell=True, cwd=tmpfolder, start_new_session=True)

        cancelled = {'value': False}

        def handle_cancel(signum, frame):
            # Celery delivers this when the task is revoked with terminate=True.
            # Kill the whole process group (not just proc.pid) so nothing is
            # left running orphaned, then let the task end.
            cancelled['value'] = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass

        previous_handler = signal.signal(signal.SIGTERM, handle_cancel)

        try:
            # Some packages (e.g. optic) redirect their real output to a file
            # via `>> plan` inside `call` - a template that comes from that
            # package's own manifest in planutils (e.g. optic's is literally
            # "optic {domain} {problem} >> plan"), not something in this repo
            # - rather than writing to the process's own stdout. So tail that
            # file on disk to observe progress while the process is still
            # running, using the same glob descriptor that's used to retrieve
            # the final output below.
            #
            # Read incrementally (seek to where the last read left off)
            # rather than re-reading the whole file every poll: a full re-read
            # each cycle means total bytes read over a run's lifetime grows
            # with run-length x poll-frequency x current-file-size, which
            # matters once a search runs long/produces a large log. The
            # accumulated content (not just each new chunk) is still what
            # gets published, since the client parses the full text for the
            # last solution block found so far.
            output_pattern = os.path.join(tmpfolder, output_file["files"])
            matched_file = None
            file_pos = 0
            accumulated_content = ""
            while proc.poll() is None:
                time.sleep(0.2)
                if matched_file is None:
                    matches = glob.glob(output_pattern)
                    if not matches:
                        continue
                    matched_file = matches[0]
                with open(matched_file, 'r') as f:
                    f.seek(file_pos)
                    new_content = f.read()
                    file_pos = f.tell()
                if not new_content:
                    continue
                accumulated_content += new_content
                if '; Plan found with metric' in new_content:
                    self.update_state(state='PROGRESS', meta={'call': call, 'partial_stdout': accumulated_content})
        finally:
            signal.signal(signal.SIGTERM, previous_handler)

        if cancelled['value']:
            shutil.rmtree(tmpfolder, ignore_errors=True)
            return {"stdout":"", "stderr":"Cancelled by client", "call":call, "output":{},"output_type":output_file["type"]},arguments

        res = SimpleNamespace(stdout=proc.stdout.read(), stderr=proc.stderr.read())

        output = retrieve_output_file(output_file, tmpfolder)
        # Remove the files in temfolder when task is finished
        shutil.rmtree(tmpfolder)
        result={"stdout":res.stdout, "stderr":res.stderr, "call":call, "output":output,"output_type":output_file["type"]}
        return result,arguments
    except SoftTimeLimitExceeded as e:
        return {"stdout":"Request Time Out", "stderr":"", "call":call, "output":{},"output_type":output_file["type"]},arguments
