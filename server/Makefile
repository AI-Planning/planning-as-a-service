
all : build-planutils-image build-start

build-planutils-image:
	docker build -t paas:latest .

db-data:
	mkdir -p db_data

build-start: db-data
	CURRENT_USER_ID="$(shell id -u)" CURRENT_GROUP_ID="$(shell id -g)" docker compose --compatibility up -d --build
