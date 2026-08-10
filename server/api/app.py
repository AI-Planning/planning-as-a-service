import os
import tempfile
from flask import Flask
from flask import url_for
from flask import flash, Markup, render_template, request, redirect, send_file, make_response, jsonify, json,abort
from flask_uploads  import (UploadSet, configure_uploads, IMAGES,
                              UploadNotAllowed)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from werkzeug.utils import secure_filename

from base64 import b64encode

from planutils.package_installation import PACKAGES
from planutils import settings
import copy

from worker import celery
import celery.states as states

# Adaptor
from adaptor.adaptor import Adaptor
from flask_cors import CORS

from collections import OrderedDict
from datetime import datetime

app = Flask(__name__)
# allow CORS for all domains on all routes
CORS(app)





cpuCount=os.cpu_count()

# Load config.py info
app.config.from_object("config")

# Secret key for flashing messages back
app.secret_key = app.config['SECRET_KEY']

# For API limit checking
block_dict={}
LIMITER_SECONDS= app.config['LIMITER_SECONDS']

# Upper bound on the per-request "max_time" override (seconds), so a client
# can't tie up a worker indefinitely.
MAX_ALLOWED_TIME = int(os.environ.get('MAX_ALLOWED_TIME', 120))

# Flask-Upload
PDDL = ('pddl',)
pddl_files = UploadSet('pddl', PDDL, default_dest=lambda x: app.config['UPLOAD_FOLDER'])
configure_uploads(app, pddl_files)

# 16 MB max size for PDDL files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# For any unexpected error, this error message will return
@app.errorhandler(500)
def internal_error(error):
    app.logger.error('Server Error: %s', (error))
    return jsonify({"error": "There was a server-side error trying to run a planutils package."})


# Solver API
@app.route('/solver/', methods=['GET', 'POST'])
def index():
    default_package="lama-first"
    if request.method == 'GET':
        # This is where we will send the user to the API documentation
        if default_package in PACKAGES:
            return jsonify(PACKAGES[default_package])
        else:
            return jsonify({"Error":"{} is not installed".format(default_package)})

    elif request.method == 'POST':
        if check_lock():
            if check_for_throttle(request.remote_addr):
                abort(429, description="Sorry, we're busy. Please try again after {} seconds.".format(LIMITER_SECONDS))

        # Called route with a package that isn't in Planutils
        if default_package not in PACKAGES:
            return jsonify({"Error":"{} is not installed".format(default_package)})

        # Grabs the request data (JSON)
        request_data = request.get_json()
        # Contains manifest information
        package_manifest = PACKAGES[default_package]['endpoint']['services']["solve"]

        # Get all necessary arguments for the service from request_data
        arguments = get_arguments(request_data, package_manifest)
        if 'Error' in arguments:
            return jsonify(arguments)

        call = package_manifest['call']
        output_file = package_manifest['return']
        # Send task
        task = celery.send_task('tasks.run.package', args=[default_package, arguments, call, output_file], kwargs={})

        # keep the IP and datetime of the tasks
        block_dict[request.remote_addr]=datetime.now()
        return jsonify({"result":str(url_for('check_task', task_id=task.id, external=True))})

# Main execution route for running planutils packages
@app.route('/package/<package>/<service>', methods=['GET', 'POST'])
def runPackage(package, service):
    # Get request
    if request.method == 'GET':
        # This is where we will send the user to the API documentation
        if package in PACKAGES:
            return jsonify(PACKAGES[package])
        else:
            return jsonify({"Error":"That package does not exist"})

    # Post request
    elif request.method == 'POST':

        if check_lock():
            if check_for_throttle(request.remote_addr):
                abort(429, description="Sorry, we're busy. Please try again after {} seconds.".format(LIMITER_SECONDS))

        # Called route with a package that isn't in Planutils
        if package not in PACKAGES:
            return jsonify({"Error":"That package does not exist"})

        if 'endpoint' not in PACKAGES[package]:
            return jsonify({"Error":"That package does not contain an API endpoint"})

        if service not in PACKAGES[package]['endpoint'].get('services',{}):
            return jsonify({"Error":"That package does not contain service " + service})

        persistent_value="true" if request.headers.get('persistent',"false") == "true" else "false"

        # Grabs the request data (JSON)
        request_data = request.get_json()
        # Contains manifest information
        package_manifest = PACKAGES[package]['endpoint']['services'][service]

        # Get all necessary arguments for the service from request_data
        arguments = get_arguments(request_data, package_manifest)
        if 'Error' in arguments:
            return jsonify(arguments)

        call = package_manifest['call']
        output_file = package_manifest['return']

        # Optional per-request override of the planner time budget, clamped to
        # avoid a client hogging a worker indefinitely.
        max_time = None
        if request_data and request_data.get('max_time') is not None:
            try:
                max_time = min(max(int(request_data['max_time']), 1), MAX_ALLOWED_TIME)
            except (TypeError, ValueError):
                return jsonify({"Error": "max_time must be an integer number of seconds"})

        # Send task
        task_kwargs = {"persistent":persistent_value, "max_time":max_time}
        send_kwargs = {"soft_time_limit": max_time + 10} if max_time else {}
        task = celery.send_task('tasks.run.package', args=[package, arguments, call, output_file], kwargs=task_kwargs, **send_kwargs)

        # keep the IP and datetime of the tasks
        block_dict[request.remote_addr]=datetime.now()
        return jsonify({"result":str(url_for('check_task', task_id=task.id, external=True))})



# Redirects user to documentation for the package
@app.route('/package')
def get_available_package():
    all_packages=copy.deepcopy(PACKAGES)
    installed_package=settings.load()['installed']
    for package in all_packages:
        all_packages[package]["package_name"]=package

    # Return the manifest of installed package
    interested_package={package: all_packages[package] for package in all_packages if package in installed_package if "services" in all_packages[package].get("endpoint", {})}
    return jsonify(interested_package)


# Redirects user to documentation for the package
@app.route('/package/<package>')
def get_request_for_package(package):
    return redirect(url_for('get_documentation', package=package))

@app.route('/docs/<package>')
def get_documentation(package):
    if package in PACKAGES:
        package_data = json.dumps(PACKAGES[package], sort_keys = True, indent = 4, separators = (',', ': '))
        return render_template('documentation.html', package_information=package_data)
    else:
        return render_template('documentation.html', package_information='No package with that name.')

@app.route('/docs/<package>/<service>')
def get_documentation_service(package, service):
    if package in PACKAGES:
        if service in PACKAGES[package]['endpoint']['services']:
            package_data = json.dumps(PACKAGES[package]['endpoint']['services'][service], sort_keys = True, indent = 4, separators = (',', ': '))
            return render_template('documentation.html', package_information=package_data)
        else:
            return render_template('documentation.html', package_information='' + package + " does not have service: " + service)
    else:
        return render_template('documentation.html', package_information='No package with that name.')


# @limiter.limit("1/10second", error_message="Sorry, we're busy. Please try again after 10 seconds.")
@app.route('/check/<string:task_id>', methods=['GET', 'POST'])
def check_task(task_id: str) -> str:
    res = celery.AsyncResult(task_id)
    if res.state == states.PENDING:
        return {"status":res.state}
    elif res.state == 'PROGRESS':
        return {"status":"PROGRESS", "partial_result":res.info}
    elif res.state == states.REVOKED:
        # Cancelled before a worker ever picked it up (e.g. still queued
        # under load) - tasks.run.package's own SIGTERM handler covers
        # cancelling an already-running task, this covers the rest.
        cancelled_result = {"stdout":"", "stderr":"Cancelled by client", "call":"", "output":{}, "output_type":"log"}
        return {"result":cancelled_result, "status":"ok"}
    else:
        #Get requst

        if request.method == 'GET':
            result,arguments=res.result
            return {"result":result,"status":"ok"}
        # Post request
        elif request.method == 'POST':
            request_data = request.get_json()
            result,arguments=res.result
            if request_data and "adaptor" in request_data:
                adaptor=Adaptor()
                try:
                    transformed_result=adaptor.get_result(request_data["adaptor"],result=result,arguments=arguments,request_data=request_data)
                    return transformed_result
                except:
                    return "Adaptor Not Found",400
            else:
                # Return the default result format
                return {"result":result,"status":"ok"}


@app.route('/cancel/<string:task_id>', methods=['POST'])
def cancel_task(task_id: str) -> str:
    # terminate=True + SIGTERM asks the worker to interrupt this specific
    # task; tasks.run.package installs its own SIGTERM handler to kill the
    # planner's whole process group, not just revoke the Celery task bookkeeping.
    celery.control.revoke(task_id, terminate=True, signal='SIGTERM')
    return {"status": "cancelled"}


# Returns all necessary arguments for a service in a package
def get_arguments(request_data, package_manifest):
    # Global package arguments
    arguments = {}

    try:
        # Service specific arguments
        if "args" in package_manifest:
            # We have extra args
            for arg in package_manifest['args']:
                # If argument_invalid is populated, we have an error
                arg_name=arg['name']
                arg_type=arg['type']
                if arg_name not in request_data:
                    # Error: Required argument was not provided
                    return {"Error":"Required argument, " + arg_name + " was not provided"}
                else:
                    arguments[arg_name] = {"value":request_data[arg_name], "type":arg_type}
        return arguments
    except:
        return {"Error": "This Planutils package is not configured correctly"}


def check_for_throttle(ip_address):
    if ip_address not in block_dict:
        return False
    last_request_time=block_dict[ip_address]
    seconds_delta=(datetime.now()-last_request_time).total_seconds()
    return seconds_delta<LIMITER_SECONDS


# The maximum number of threads for a worker is same as the CPU counts.
def check_lock():
    working_node = celery.control.inspect()
    total_tasks=0
    active_nodes=working_node.active()
    for worker in active_nodes:
        num_active_tasks=len(active_nodes[worker])
        total_tasks+=num_active_tasks
    # Make sure always one thread is available for new caller
    if total_tasks >= cpuCount -1:
        return True
    else:
        return False


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
