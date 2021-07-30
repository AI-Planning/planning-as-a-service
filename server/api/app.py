import os
import tempfile
from flask import Flask
from flask import url_for
from flask import flash, Markup, render_template, request, redirect, send_file, make_response, jsonify, json
from flask_uploads  import (UploadSet, configure_uploads, IMAGES,
                              UploadNotAllowed)

from werkzeug.utils import secure_filename

from base64 import b64encode

from planutils.package_installation import PACKAGES

from worker import celery
import celery.states as states

app = Flask(__name__)

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
def index():
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':

        # Get files
        form_problem = request.files["problem-file"]
        form_domain = request.files["domain-file"]

        # Check that files were provided
        if form_problem.filename == '' or form_domain.filename == '':
            flash('No selected file')
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
def runPackage(package, service):
    # Get request
    if request.method == 'GET':
        # This is where we will send the user to the API documentation
        return redirect(url_for('get_documentation', package=package))
    
    # Post request
    elif request.method == 'POST':
        # Called route with a package that isn't in Planutils
        if package not in PACKAGES:
            return jsonify({"Error":"That package does not exist"})
        
        if service not in PACKAGES[package]['endpoint']['services']:
            return jsonify({"Error":"That package does not contain service " + service})
        
        if 'endpoint' not in PACKAGES[package]:
            return jsonify({"Error":"That package does not contain an API endpoint"})
        
        # Grabs the request data (JSON)
        request_data = request.get_json()
        # Contains manifest information
        package_manifest = PACKAGES[package]['endpoint']
        
        # If its a generic solver, we can make assumptions
        if service == 'solve' and package_manifest['type'] == 'solver':
            if 'domain' not in request_data:
                return jsonify({"Error":"Missing required argument: domain"})
            if 'problem' not in request_data:
                return jsonify({"Error":"Missing required argument: problem"})
            
            arguments = {'domain':{"value":request_data['domain'], "type":"file"}, 'problem':{"value":request_data['problem'], "type":"file"}}
        else:
            # Get all necessary arguments for the service from request_data
            arguments = get_arguments(package, service, request_data, package_manifest)
            if 'Error' in arguments:
                return arguments
            
        call = package_manifest['services'][service]['call']
        output_file = package_manifest['services'][service]['return']
        # Send task
        task = celery.send_task('tasks.run.package', args=[package, arguments, call, output_file], kwargs={})
        return jsonify({"result":str(url_for('check_task', task_id=task.id, external=True))})

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

@app.route('/check/<string:task_id>')
def check_task(task_id: str) -> str:
    res = celery.AsyncResult(task_id)
    if res.state == states.PENDING:
        return res.state
    else:
        return {"result":res.result}
    
# Returns all necessary arguments for a service in a package
def get_arguments(package, service, request_data, package_manifest):
    # Global package arguments
    arguments = {}
    for arg in package_manifest['args']:
        argument_invalid = validate_argument(arguments, arg, request_data)
        if argument_invalid:
            return argument_invalid
    
    # Service specific arguments
    if "args" in package_manifest['services'][service]:
        # We have extra args
        for arg in package_manifest['services'][service]['args']:
            # If argument_invalid is populated, we have an error
            argument_invalid = validate_argument(arguments, arg, request_data)
            if argument_invalid:
                return argument_invalid
            
    return arguments

# Validates an argument, throws error response if 
def validate_argument(arguments, arg, request_data):
    if arg['name'] not in request_data:
        if 'default' in arg:
            arguments[arg['name']] = {"value":arg['default'], "type":arg['type']}
        else:
            # Error: Required argument was not provided
            return jsonify({"Error":"Required argument, " + arg['name'] + " was not provided"})
    else:
        arguments[arg['name']] = {"value":request_data[arg['name']], "type":arg['type']}

if __name__ == "__main__":

    app.run("0.0.0.0", port=5001, debug=True)
