# Ways to Run & Debug Server

## Docker Build & Launch

Get sources

```bash
git clone https://github.com/AI-Planning/planning-as-a-service
cd planning-as-a-service/server
```

Set up .env file:

Please create a new environment file called .env, and set up the following variable. You can reference the provided `.env.example` file.

* FLOWER_USERNAME=username #Flower Moinitor Username
* FLOWER_PASSWORD=password #Flower Moinitor Password
* MAX_MEMORY_PER_CHILD=12000 # Max memory can be allocated a task
* TIME_LIMIT=180 #Time limit per task

Start Docker:

```bash
docker-compose up -d --build
```

or

```bash
make build-start
```

This will expose the Flask application's endpoints on port `5001` as well as a [Flower](https://github.com/mher/flower) server for monitoring workers on port `5555`

To add more workers:

```bash
docker-compose up -d --scale worker=5 --no-recreate
```

To shut down:

```bash
docker-compose down
```

To change the endpoints, update the code in [api/app.py](api/app.py)

Task changes should happen in [queue/tasks.py](celery-queue/tasks.py)



## API

- Planning solver: [localhost:5001/solver/](http://localhost:5001/solver/)
- Queue Monitor: [localhost:5555](http://localhost:5555)

## Local Dev

Assuming you are in the `server/` directory.

```bash
sudo apt-get install redis-server
sudo service redis-server start
virtualenv env
pip install -r requirements.txt
```

### Run server

New terminal (If you are using vscode, do ```CTRL+SHIFT+` ``` to open a new terminal)

Run Flask:

```bash
source env/bin/activate
cd api
python app.py
```

New terminal and start celery:

```bash
source env/bin/activate
cd celery-queue
celery -A tasks worker --loglevel=info
```

New Terminal and start flower (queue monitoring):

```bash
source env/bin/activate
cd celery-queue
flower -A tasks --port=5555 --broker=redis://localhost:6379/0
```

### Debug

Go to `server` folder and open `vscode`. Install vscode first. Note that this assumes you have started celery and flower as instructed above.

```bash
cd server
code . &
```

Go to the debug symbol add breakpoints and debug as shown below:
![image](https://github.com/AI-Planning/planning-as-a-service/blob/master/docs/videos/debug.gif)

### Planutils 

We can execute Planutils packages with the defined API

`http://localhost:5001/package/{package_name}/{package_service}`

The required arguments for the POST request are defined in the Planutils package manifests, and can be easily viewed at: 

`http://localhost:5001/docs/{package_name}`
### Update Planutils on the server
Once you have login to the Ubuntu server.

1.List all the containers:
`
sudo docker container ls -a
`
![image](https://github.com/AI-Planning/planning-as-a-service/blob/planutils-functionality/docs/videos/containers.png)

2.We have to update planutils in the `server_worker` and `server_web` containers. You have to run commands 2.1 to 2.4 for both container.

2.1 Use the following command to login to the container:
`sudo docker exec -it containerID bash`

2.2 In the container terminal, type the following command to update the latest planutils on the `manifest-new-version` branch.
```
git clone https://github.com/AI-Planning/planutils.git
cd planutils
git checkout manifest-new-version
pip uninstall planutils
python3 setup.py install --old-and-unmanageable
planutils setup
```
2.3 Then install the planner using the following command:
```
planutils install plannername
```

2.4 Leave the container use `exit`


### Example use

A simple python script to send a POST request to the lama-first planner, getting back stdout, stderr, and the generated plan:

```
import requests
import time
from pprint import pprint

req_body = {
    "domain":"(define (domain BLOCKS) (:requirements :strips) (:predicates (on ?x ?y) (ontable ?x) (clear ?x) (handempty) (holding ?x) ) (:action pick-up :parameters (?x) :precondition (and (clear ?x) (ontable ?x) (handempty)) :effect (and (not (ontable ?x)) (not (clear ?x)) (not (handempty)) (holding ?x))) (:action put-down :parameters (?x) :precondition (holding ?x) :effect (and (not (holding ?x)) (clear ?x) (handempty) (ontable ?x))) (:action stack :parameters (?x ?y) :precondition (and (holding ?x) (clear ?y)) :effect (and (not (holding ?x)) (not (clear ?y)) (clear ?x) (handempty) (on ?x ?y))) (:action unstack :parameters (?x ?y) :precondition (and (on ?x ?y) (clear ?x) (handempty)) :effect (and (holding ?x) (clear ?y) (not (clear ?x)) (not (handempty)) (not (on ?x ?y)))))",
    "problem":"(define (problem BLOCKS-4-0) (:domain BLOCKS) (:objects D B A C ) (:INIT (CLEAR C) (CLEAR A) (CLEAR B) (CLEAR D) (ONTABLE C) (ONTABLE A) (ONTABLE B) (ONTABLE D) (HANDEMPTY)) (:goal (AND (ON D C) (ON C B) (ON B A))) )"
}

solve_request = requests.post("http://localhost:5001/package/lama-first/solve", json=req_body).json()

celery_result = requests.get('http://localhost:5001' + solve_request['result'])

print('Computing...')
while celery_result.text == 'PENDING':
	celery_result = requests.get('http://localhost:5001' + solve_request['result'])
	time.sleep(0.5)

pprint(celery_result.json())
```

This python code will run a test POST request on the lama-first solver, and return the link to access the result from the celery queue. In the meantime, the program 
polls for the task to be completed, and prints out the returned json when it is. 

* Note: This script needs to be run in the same environment as the docker container


## Docker Flask Celery Redis

A basic [Docker Compose](https://docs.docker.com/compose/) template for orchestrating a [Flask](http://flask.pocoo.org/) application & a [Celery](http://www.celeryproject.org/) queue with [Redis](https://redis.io/)

---

Docker structure adapted from [https://github.com/mattkohl/docker-flask-celery-redis](https://github.com/mattkohl/docker-flask-celery-redis)
