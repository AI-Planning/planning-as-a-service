# Docker Flask Celery Redis

A basic [Docker Compose](https://docs.docker.com/compose/) template for orchestrating a [Flask](http://flask.pocoo.org/) application & a [Celery](http://www.celeryproject.org/) queue with [Redis](https://redis.io/)

---

adapted from [https://github.com/mattkohl/docker-flask-celery-redis](https://github.com/mattkohl/docker-flask-celery-redis)

## Get sources

```bash
git clone https://github.com/AI-Planning/planning-as-a-service
```

## Docker Build & Launch

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

# API

- Planning solver: [localhost:5001/solver/](localhost:5001/solver/) 
- Queue Monitor: [localhost:5555](localhost:5555)

# Local Dev



```
pip install -r requirements.txt
sudo apt-get install redis-server
sudo service redis-server start
```

## Run server


New terminal (If you are using vscode, do ```CTRL+SHIFT+` ``` to open a new terminal)

Run Flask:
```
source env/bin/activate
cd api
python app.py
```

New terminal and start celery
```
source env/bin/activate
cd celery-queue
celery -A tasks worker --loglevel=info
```

New Terminal and start flower (queue monitoring)

```
source env/bin/activate
flower -A tasks --port=5555 --broker=redis://localhost:6379/0
```



## Debug

Go to `server` folder and open `vscode`. Install vscode first.

```
cd server
code . &
```

Go to the debug symbol add breakpoints and debug as shown below:
![image](/docs/videos/debug.gif)

## Planutils (NOT WORKING)
planutils fails to setup in a python virtual environment:

```
sudo apt install singularity
planutils setup
planutils install lama
```

Yoy get

```
 planutils install lama

About to install the following packages: downward (36M), lama (20K)
  Proceed? [Y/n] Y
Installing downward...
Singularity 1.0b1 (commit: b0d3406e311f4ac3aa6f4d0187f32926b3808fef)
Running under Python 3.8.2 (default, Apr 27 2020, 15:53:34) [GCC 9.3.0]
pygame 1.9.6
Hello from the pygame community. https://www.pygame.org/contribute.html
The error-log configured as /home/nirlipo/.local/share/singularity/log/error.log (lazily created when something is logged)
Usage: singularity [options]

singularity: error: no such option: --name

Error installing downward. Rolling back changes...

```

If you remove the --name from ```env/lib/plauntils/packages/downward/install``` the installation proceeds but fails after few seconds:

```
$ planutils install lama

About to install the following packages: downward (36M), lama (20K)
  Proceed? [Y/n] Y
Installing downward...
Singularity 1.0b1 (commit: b0d3406e311f4ac3aa6f4d0187f32926b3808fef)
Running under Python 3.8.2 (default, Apr 27 2020, 15:53:34) [GCC 9.3.0]
pygame 1.9.6
Hello from the pygame community. https://www.pygame.org/contribute.html
The error-log configured as /home/nirlipo/.local/share/singularity/log/error.log (lazily created when something is logged)


Fatal Python error: (pygame parachute) Segmentation Fault
Python runtime state: initialized

Current thread 0x00007fc2b0788740 (most recent call first):
  File "/usr/lib/python3/dist-packages/singularity/__init__.py", line 346 in main
  File "/usr/games/singularity", line 11 in <module>
./install: line 3:  4445 Aborted                 singularity pull downward.sif shub://aibasel/downward

Error installing downward. Rolling back changes...
rm: cannot remove 'downward.sif': No such file or directory
```


