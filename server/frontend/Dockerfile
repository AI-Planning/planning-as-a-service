FROM planutils:latest

ENV HOST 0.0.0.0
ENV PORT 80
ENV DEBUG true

COPY . /frontend
COPY ../requirements.txt /api/requirements.txt
WORKDIR /frontend

RUN apt-get update
RUN apt-get install -y python3-dev

# install requirements
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install -r requirements.txt

# expose the app port
EXPOSE 80

RUN pip install gunicorn

# # run the app server. If you need https, use the command below instead.
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

# # run the app server with https.
# # CMD ["gunicorn", "--bind", "0.0.0.0:80", "--certfile", "/etc/letsencrypt/live/paas-uom.org/fullchain.pem", "--keyfile", "/etc/letsencrypt/live/paas-uom.org/privkey.pem", "app:app"]
