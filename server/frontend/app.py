import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='/')
# allow CORS for all domains on all routes
CORS(app)


# Hello world index
@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/legacy')
def legacy():
    # Render the legacy.html
    return render_template('legacy.html')


# return a json error if the send a POST to /solve
@app.route('/solve', methods=['POST'])
def solve():
    return jsonify({'error': 'This is a legacy endpoint. Please see solver.planning.domains for updated usage.'}), 400


if __name__ == "__main__":
    app.run("0.0.0.0", port=80, debug=True)
