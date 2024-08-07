all : build-planutils-image build-start

build-planutils-image:
	docker build -t paas:latest .

build-start: # install and start
	docker compose --compatibility up -d --build
