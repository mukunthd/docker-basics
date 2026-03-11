# Basics of Docker 

# Build Docker Image By Running the Following Command

$docker build -t jenkinsdemo . # -t = Tag 


# To Run Containers

$docker run -it -p 2222:8080 jenkinsdemo # -i = interactive ; -t terminal

# In host's browser type 

localhost:2222 for Jenkins Setup

# Some of the Docker Commands

docker images --> to list the images

docker ps  --> to see the running containers

docker ps -a --> to see all the containers which are exited 

docker run -it <image_tag> --> to run the image which will create containers 

docker run -it <image_tag> bash --> to run the image in bash

docker exec -it <container_tag> bash --> this is to log into the running container in bash (edited)

docker run -it -p 8080:8080 <image_tag> --> this is to run the image using the port 8080 in host(ubuntu) and 8080 in container 

DOCKER CHEATSHEET - https://github.com/wsargent/docker-cheat-sheet#dockerfile












