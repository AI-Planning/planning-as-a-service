# Stage 0: Build Celery worker

FROM planutils:latest 


ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0

ENV C_FORCE_ROOT true
ENV WEB_DOCKER_URL web
ENV PATH=$PATH:~/.planutils/bin

COPY . /queue
WORKDIR /queue

RUN apt-get update
RUN apt-get install -y libmysqlclient-dev python3-dev build-essential

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install -r requirements.txt