FROM paas:latest

ENV HOST 0.0.0.0
ENV PORT 80
ENV DEBUG true

COPY . /frontend
WORKDIR /frontend

# expose the app port
EXPOSE 80

RUN pip install gunicorn

# # run the app server. If you need https, use the command below instead.
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

# # run the app server with https.
# # CMD ["gunicorn", "--bind", "0.0.0.0:80", "--certfile", "/etc/letsencrypt/live/paas-uom.org/fullchain.pem", "--keyfile", "/etc/letsencrypt/live/paas-uom.org/privkey.pem", "app:app"]
