# Docker Flask Celery Redis

A basic [Docker Compose](https://docs.docker.com/compose/) template for orchestrating a [Flask](http://flask.pocoo.org/) application & a [Celery](http://www.celeryproject.org/) queue with [Redis](https://redis.io/)

---

adapted from [https://github.com/mattkohl/docker-flask-celery-redis](https://github.com/mattkohl/docker-flask-celery-redis)

### Installation

```bash
git clone https://github.com/AI-Planning/planning-as-a-service
```

### Build & Launch

```bash
cd plannin-as-a-service/server
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

### Test

[localhost:5001/solver/](http://localhost:5001/solver/) is my failed attempt to put things together.

to test things are working, see other APIs in app.py. For example: [localhost:5001/add/1/2](http://localhost:5001/add/1/2) will trigger a worker, and you can see the trace in the monitoring system [localhost:5555](http://localhost:5555)

Need to figure out how to debug using docker images. The current requirements used are not compatible with python3.8.

I tried this but didn't work: https://blog.theodo.com/2020/05/debug-flask-vscode/ maybe someone else can put things togehter. More later :)

