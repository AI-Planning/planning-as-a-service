import os
from flask import Flask
from flask import url_for
from flask import flash, Markup, render_template, request, redirect, send_file
from flask_uploads  import (UploadSet, configure_uploads, IMAGES,
                              UploadNotAllowed)

from werkzeug.utils import secure_filename

from base64 import b64encode


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
        solvers = {"lama","bfws"}
        for solver in solvers:
            task = celery.send_task('tasks.solve', args=[domain_url, problem_url, solver], kwargs={})
            flash( Markup(f"Sovling domain <a href='{domain_url}'> uploaded_domain </a> and <a href='{problem_url}'> uploaded_problem </a>: Task ID: {task.id} - <a href='{url_for('check_task', task_id=task.id, external=True)}'>check status of {task.id} </a>"))

        # remove the tmp/fies
        # This may fail if celery tasks have not finished. May happen while debugging, or in deployed version.
        # TODO: Find out if there's an async way of removing files once celery tasks have finished
        #       Something similar to what's there in function `check_task` below
        # os.remove( pddl_files.path(filename_domain) )
        # os.remove( pddl_files.path(filename_problem) )

        return redirect(url_for('index'))

@app.route('/check/<string:task_id>')
def check_task(task_id: str) -> str:
    res = celery.AsyncResult(task_id)
    if res.state == states.PENDING:
        return res.state
    else:
        return str(res.result)


if __name__ == "__main__":

    app.run("0.0.0.0", port=5001, debug=True)
