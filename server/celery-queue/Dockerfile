# Stage 0: Build Celery worker

FROM python:3.8-alpine

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true
ENV WEB_DOCKER_URL web

COPY . /queue
WORKDIR /queue

RUN pip install -r requirements.txt

ENTRYPOINT celery -A tasks worker --loglevel=info