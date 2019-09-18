FROM ubuntu:latest

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
RUN ln -s /usr/share/zoneinfo/Etc/GMT+7 /etc/localtime

ENV LANG en_US.utf8

RUN apt-get update
RUN apt-get install docker-ce docker-ce-cli containerd.io

FROM python:3.7
# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

RUN apt update \
    && apt install -y git python3 \
    python3-pip \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    python3-tk

# Run the gunicorn
RUN gunicorn --workers=3 --threads=3 --worker-connections=1000 websockets.core.app:app --bind 0.0.0.0:8000 --worker-class aiohttp.worker.GunicornWebWorker