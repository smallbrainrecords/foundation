#FROM python:2 
FROM ubuntu:18.04
#FROM node:12-buster

WORKDIR /usr/src/smallbrains-app

COPY requirements.txt .

RUN apt update \ 
  && apt install -y curl python2.7 \
  && curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py \
  && python2.7 get-pip.py 

RUN apt-get update

RUN apt-get install -y libmysqlclient-dev
RUN apt-get install -y libpq-dev python-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libffi-dev


RUN apt-get install -y \
  nodejs-dev \
  node-gyp \
  npm 
#   python-dev \
#   libxml2-dev \
#   libxslt1-dev \
#   libldap2-dev \
#   libffi-dev \
#   libsasl2-dev \
#   libpcap-dev \ 
#   libpq-dev \
#   build-essential \
#   manpages-dev \
#   libmysqlclient-dev \
#   default-libmysqlclient-dev 

RUN pip install pathlib
RUN pip install mysql-connector-python
RUN pip install -r requirements.txt

COPY . .

RUN cd ./static && npm install

#RUN apt-get update -y; apt install build-essential ; apt-get install manpages-dev
#RUN apt-get update ; apt install build-essential ; apt-get install manpages-dev; apt-get install -y default-libmysqlclient-dev
#RUN python -m pip install --no-binary MySQL-python MySQL-python
#RUN pip install mysqlclient

ENV DATABASE_NAME=smallbrainsDB
ENV DATABASE_TEST_NAME=smallbrainsDB-test
ENV DATABASE_USER=root
ENV DATABASE_PASSWORD=root
ENV DATABASE_HOST=localhost
ENV DATABASE_PORT=3306
ENV SECRET_KEY=c388dd0d186b6497d6dfc05187fb6c5f41e17676f166737798eb3b503b9f6218c04ed30c37527f454c8fa85c56053ab2bcdb83daf01b93a5101260359ab2201a
# Install node and dependencies ('./static/')

EXPOSE 8000

CMD ["tail", "-f", "/dev/null"]

# CMD [ "python", "/usr/src/smallbrains-app/manage.py runserver" ]