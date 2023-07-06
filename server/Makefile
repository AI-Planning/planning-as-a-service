all : build-planutils-image build-start

build-planutils-image:
	docker build -t planutils:latest .

build-start: # install and start
	docker compose --compatibility up -d --build 
