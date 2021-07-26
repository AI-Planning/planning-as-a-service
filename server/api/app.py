import os
import tempfile
from flask import Flask
from flask import url_for
from flask import flash, Markup, render_template, request, redirect, send_file, make_response, jsonify
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
            #  Want to provide the name associated with the manifest
        solvers = {"lama-first"}
        for solver in solvers:
            task = celery.send_task('tasks.solve', args=[domain_url, problem_url, solver], kwargs={})
            flash( Markup(f"Solving domain <a href='{domain_url}'> uploaded_domain </a> and <a href='{problem_url}'> uploaded_problem </a>: Task ID: {task.id} - <a href='{url_for('check_task', task_id=task.id, external=True)}'>check status of {task.id} </a>"))
        # remove the tmp/files
        # This may fail if celery tasks have not finished. May happen while debugging, or in deployed version.
        # TODO: Find out if there's an async way of removing files once celery tasks have finished
        #       Something similar to what's there in function `check_task` below
        # os.remove( pddl_files.path(filename_domain) )
        # os.remove( pddl_files.path(filename_problem) )

        return redirect(url_for('index'))
    
@app.route('/package/<package>/<service>', methods=['GET', 'POST'])
def runPackage(package, service):
    # Get request
    if request.method == 'GET':
        # This is where we will send the user to the API documentation
        return jsonify({PACKAGES[package]})
    
    # Post request
    elif request.method == 'POST':
        # Called route with a package that isn't in Planutils
        if package not in PACKAGES:
            return make_response("That package does not exist.", 400)
        
        if service not in PACKAGES[package]['endpoint']['services']:
            return make_response("That package does not offer service: " + service, 400)
        
        # Grabs the request data (JSON)
        request_data = request.get_json()
        # Contains manifest information
        package_manifest = PACKAGES[package]['endpoint']
        
        # If its a generic solver, we can make assumptions
        if service == 'solve' and package_manifest['type'] == 'solver':
            domain = request_data['domain']
            problem = request_data['problem']
            task = celery.send_task('tasks.solve.string', args=[domain, problem, package], kwargs={})
        else:
            # Global package arguments
            arguments = {}
            for arg in package_manifest['args']:
                name = arg['name']
                arguments[name] = {"value":request_data[name], "type":arg['type']}
            
            # Service specific arguments
            if "args" in package_manifest['services'][service]:
                # We have extra args
                for arg in package_manifest['services'][service]['args']:
                    name = arg['name']
                    arguments[name] = {"value":request_data[name], "type":arg['type']}
            
            # Arguments now contains {arg -> value} for each argument that is needed for the service
            
            call = package_manifest['services'][service]['call']
            output_files = package_manifest['services'][service]['return']['file']
            # Send task
            task = celery.send_task('tasks.run.package', args=[package, arguments, call, [output_files]], kwargs={})
            
        return jsonify({"result":str(url_for('check_task', task_id=task.id, external=True))})

@app.route('/docs/<package>', methods=['GET'])
def get_documentation(package):
    # Just return the manifest for now
    return {PACKAGES[package]}

@app.route('/check/<string:task_id>')
def check_task(task_id: str) -> str:
    res = celery.AsyncResult(task_id)
    if res.state == states.PENDING:
        return res.state 
    else:
        return {"result":res.result}


if __name__ == "__main__":

    app.run("0.0.0.0", port=5001, debug=True)
