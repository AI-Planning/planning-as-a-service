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

# Limiter for DDOS attach

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1/10second"]
)


# For API limit checking
block_dict={}
recent_ip=[]
cpuCount=os.cpu_count()

# Load config.py info
app.config.from_object("config")

# Secret key for flashing messages back
app.secret_key = app.config['SECRET_KEY']

# Flask-Upload
PDDL = ('pddl',)
pddl_files = UploadSet('pddl', PDDL, default_dest=lambda x: app.config['UPLOAD_FOLDER'])
configure_uploads(app, pddl_files)

# 16 MB max size for PDDL files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Solver API
@app.route('/solver/', methods=['GET', 'POST'])
@limiter.limit("1/10second", error_message="Sorry, we're busy. Please try again after 10 seconds.")
def index():
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':

        # Get files
        form_domain = request.files["domain"]
        form_problem = request.files["problem"]
        
        # Check that files were provided
        if form_problem.filename == '' or form_domain.filename == '':
            flash('Domain or Problem file is missing')
            return redirect(request.url)

        # Save file with Flask-upload
        try:
            filename_domain = pddl_files.save(form_domain)
            filename_problem = pddl_files.save(form_problem)
        except UploadNotAllowed:
            flash("The upload was not allowed")
            return redirect(request.url)

        # Files URL to send celery
        domain_url = pddl_files.url(filename_domain)
        problem_url = pddl_files.url(filename_problem)

        # Test to call celery with a couple of solvers
        solvers = {"lama-first"}
        for solver in solvers:
            task = celery.send_task('tasks.solve', args=[domain_url, problem_url, solver], kwargs={})
            flash( Markup(f"Solving domain <a href='{domain_url}'> uploaded_domain </a> and <a href='{problem_url}'> uploaded_problem </a>: Task ID: {task.id} - <a href='{url_for('check_task', task_id=task.id, external=True)}'>check status of {task.id} </a>"))
        # remove the tmp/files
        # This may fail if celery tasks have not finished. May happen while debugging, or in deployed version.
        
        return redirect(url_for('index'))

# Main execution route for running planutils packages
@app.route('/package/<package>/<service>', methods=['GET', 'POST'])
@limiter.exempt
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
        print(datetime.now(),block_dict.get(request.remote_addr,0),flush=True)
        if check_for_throttle(request.remote_addr):
            abort(429, description="Sorry, we're busy. Please try again after 20 seconds.")
        elif check_lock():
            server_in_contention()

        # Called route with a package that isn't in Planutils
        if package not in PACKAGES:
            return jsonify({"Error":"That package does not exist"})
        
        if 'endpoint' not in PACKAGES[package]:
            return jsonify({"Error":"That package does not contain an API endpoint"})

        if service not in PACKAGES[package]['endpoint']['services']:
            return jsonify({"Error":"That package does not contain service " + service})
        
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
        # Send task
        task = celery.send_task('tasks.run.package', args=[package, arguments, call, output_file], kwargs={})

        # keep the IP and datetime of the tasks
        recent_ip.append(request.remote_addr)
        return jsonify({"result":str(url_for('check_task', task_id=task.id, external=True))})



# Redirects user to documentation for the package
@app.route('/package')
@limiter.limit("1/10second", error_message="Sorry, we're busy. Please try again after 10 seconds.")
def get_available_package():
    all_packages=copy.deepcopy(PACKAGES)

    installed_package=settings.load()['installed']
    for package in all_packages:
        all_packages[package]["package_name"]=package
    
    # Return the manifest of installed package
    insterested_package=[all_packages[package] for package in all_packages if package in installed_package if "solve" in all_packages[package].get("endpoint", {}).get("services", {}) ]
    return jsonify(insterested_package)


# Redirects user to documentation for the package
@app.route('/package/<package>')
@limiter.limit("1/10second", error_message="Sorry, we're busy. Please try again after 10 seconds.")
def get_request_for_package(package):
    return redirect(url_for('get_documentation', package=package))

@app.route('/docs/<package>')
@limiter.limit("1/10second", error_message="Sorry, we're busy. Please try again after 10 seconds.")
def get_documentation(package):
    if package in PACKAGES:
        package_data = json.dumps(PACKAGES[package], sort_keys = True, indent = 4, separators = (',', ': '))
        return render_template('documentation.html', package_information=package_data)
    else:
        return render_template('documentation.html', package_information='No package with that name.')
    
@app.route('/docs/<package>/<service>')
@limiter.limit("1/10second", error_message="Sorry, we're busy. Please try again after 10 seconds.")
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
@limiter.exempt
def check_task(task_id: str) -> str:
    res = celery.AsyncResult(task_id)
    if res.state == states.PENDING:
        return {"status":res.state}
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
    
# Returns all necessary arguments for a service in a package
def get_arguments(request_data, package_manifest):
    # Global package arguments
    arguments = {}    
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

def check_for_throttle(ip_address):
    if ip_address not in block_dict:
        return False
    last_request_time=block_dict[ip_address]
    seconds_delta=(datetime.now()-last_request_time).total_seconds()
    return seconds_delta<20


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
def server_in_contention():
    for ip in recent_ip:
        block_dict[ip]=datetime.now()
    recent_ip.clear()
    
if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
