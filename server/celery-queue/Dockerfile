# Stage 0: Build Celery worker

FROM paas:latest


ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0

ENV C_FORCE_ROOT true
ENV WEB_DOCKER_URL web
ENV PATH=$PATH:~/.planutils/bin

COPY . /queue
WORKDIR /queue
