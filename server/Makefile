#default values
workers ?=12 

# 1. use make development to build/restart local development envinroment
development : build-planutils-image build-stack

# 2. build/restart application
deploy:build-planutils-image build-stack add-worker

# 3. pull the latest planutils from Dockerhub and restart the application
deploy-nocache: build-planutils-image-nocache build-stack add-worker

# 4. shutdown the whole services and delete all containers
shutdown:
	docker-compose down

build-planutils-image:
	docker build -t planutils:latest .

build-planutils-image-nocache:
	docker build --no-cache -t planutils:latest .


build-stack: 
	docker-compose up -d --build 

add-worker:
	docker-compose up -d --scale worker=$(workers) --no-recreate

