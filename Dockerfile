FROM ubuntu:latest
EXPOSE 6379

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
RUN ln -s /usr/share/zoneinfo/Etc/GMT+7 /etc/localtime

ENV LANG en_US.utf8

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
    python3-tk redis-server

RUN pip3 install --upgrade pip

RUN git clone https://github.com/lamhai1401/dj_ws_aio

WORKDIR /dj_ws_aio
COPY . /usr/local/src/dj_ws_aio
WORKDIR /usr/local/src/dj_ws_aio
ENV PYTHONPATH /usr/local/src/dj_ws_aio

RUN pip3 install -r requirements.txt

# Run the gunicorn
ENTRYPOINT ["/bin/bash", "run.sh"]