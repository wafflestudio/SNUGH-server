#!/bin/bash
git pull
sudo docker-compose down
sudo docker-compose up -d
