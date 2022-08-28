# Stage 0: Build Celery worker

FROM planutils:latest 


ENV CELERY_BROKER_URL redis://redis:6379/0
# ENV CELERY_RESULT_BACKEND redis://redis:6379/0

ENV CELERY_RESULT_BACKEND db+mysql://user:password@mysql:3306/db
ENV C_FORCE_ROOT true
ENV WEB_DOCKER_URL web
ENV PATH=$PATH:~/.planutils/bin

COPY . /queue
WORKDIR /queue

RUN apt-get update
RUN apt-get install -y libmysqlclient-dev

RUN pip install -r requirements.txt