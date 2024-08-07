FROM paas:latest

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0

ENV C_FORCE_ROOT true

ENV HOST 0.0.0.0
ENV PORT 5001
ENV DEBUG true

COPY . /api
WORKDIR /api

# expose the app port
EXPOSE 5001

RUN pip install gunicorn

# # run the app server. If you need https, use the command below instead.
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "3", "app:app"]

# # run the app server with https.
# # CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "3", "--certfile", "/etc/letsencrypt/live/paas-uom.org/fullchain.pem", "--keyfile", "/etc/letsencrypt/live/paas-uom.org/privkey.pem", "app:app"]
