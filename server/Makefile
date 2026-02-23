
all : build-planutils-image build-start

build-planutils-image:
	DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t paas:latest .

db-data:
	mkdir -p db_data

build-start: db-data
	DOCKER_DEFAULT_PLATFORM=linux/amd64 CURRENT_USER_ID="$(shell id -u)" CURRENT_GROUP_ID="$(shell id -g)" docker compose --compatibility up -d --build
