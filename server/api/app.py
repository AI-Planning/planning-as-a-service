from flask import Flask
from flask import url_for
from flask import flash, render_template, request, redirect, send_file
from werkzeug.utils import secure_filename

from worker import celery
import celery.states as states

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'pddl'}
URL = "localhost:5001"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/solver/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':
        
        f_problem = request.files["problem-file"]
        f_domain = request.files["domain-file"]

        if f_problem.filename == '' or f_domain.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Save files. Need to pass the url to celery
        problem_tmp = ""
        domain_tmp = "" 
        if file and allowed_file(domain.filename):
                filename = secure_filename(file.filename)
                domain_tmp = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
                file.save( domain_tmp )
            
        if file and allowed_file(problem.filename):
            filename = secure_filename(file.filename)
            problem_tmp = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
            file.save( problem_tmp )
                            
        #task = celery.send_task('tasks.solve', args=[f"{URL}/{problem_tmp}", f"{URL}/{domain_tmp}"], kwargs={})
        task = ""
        #flash(f"Sovling domain {f_domain.filename} and problem {f_problem.filename}")
        
        #return redirect(url_for('index'))
        return f"Sovling domain {URL}/{problem_tmp} and problem {URL}/{domain_tmp}: {task}"

@app.route('/add/<int:param1>/<int:param2>')
def add(param1: int, param2: int) -> str:
    task = celery.send_task('tasks.add', args=[param1, param2], kwargs={})
    response = f"<a href='{url_for('check_task', task_id=task.id, external=True)}'>check status of {task.id} </a>"
    return response


@app.route('/check/<string:task_id>')
def check_task(task_id: str) -> str:
    res = celery.AsyncResult(task_id)
    if res.state == states.PENDING:
        return res.state
    else:
        return str(res.result)


if __name__ == "__main__":

    app.run("0.0.0.0", debug=True)