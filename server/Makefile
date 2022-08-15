# 1. use make to build the stack first time
all : build-planutils-image build-stack add-worker

# 2. Use make rebuild when the planutils docker image is updated
rebuild: build-planutils-image-nocache build-stack add-worker

# 3. restart the whole services
restart: build-stack add-worker

# 4. shutdown the whole services
shutdown:
	docker-compose down

build-planutils-image:
	docker build -t planutils:latest .


build-planutils-image-nocache:
	docker build --no-cache -t planutils:latest .


build-stack: 
	docker-compose up -d --build 

add-worker:
	docker-compose up -d --scale worker=12 --no-recreate

