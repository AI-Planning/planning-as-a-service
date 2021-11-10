sudo apt-get update
sudo apt install docker.io
sudo apt install docker-compose
git clone https://github.com/AI-Planning/planning-as-a-service.git
cd planning-as-a-service/
git checkout planutils-functionality
cd server
sudo docker-compose up -d



# To list the runing container
sudo docker container ls -a

# To enter a container
# sudo docker exec -it 179f6fc19bec bash
sudo docker exec -it containerID bash

# leave container
exit

# restart dockers
sudo docker-compose restart