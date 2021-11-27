#!/bin/bash
cd SNUGH-server
git pull
sudo docker-compose down
sudo docker-compose up -d