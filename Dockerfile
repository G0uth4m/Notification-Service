FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install python3 python3-pip

WORKDIR /notification_service
COPY . /notification_service

RUN pip3 install -r requirements.txt