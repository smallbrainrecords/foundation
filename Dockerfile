FROM ubuntu:18.04

# Set environment variables
ENV DATABASE_NAME=smallbrains_development
ENV DATABASE_TEST_NAME=smallbrains_test
ENV DATABASE_USER=root
ENV DATABASE_PASSWORD=root
ENV DATABASE_HOST=172.17.0.1
ENV DATABASE_PORT=3306
ENV SECRET_KEY=secret

WORKDIR /usr/src/smallbrains-app

# Install python 2.7
RUN apt update \ 
  && apt install -y curl python2.7 \
  && curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py \
  && python2.7 get-pip.py 

# Install mysql client
RUN apt-get update
RUN apt-get install -y libmysqlclient-dev
RUN apt-get install -y libpq-dev python-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libffi-dev

# Install npm
RUN apt install npm -y
RUN npm install -g npm@latest-6

# Install python requirements
COPY requirements.txt .
RUN pip install pathlib
RUN apt-get install -y libmysqlclient-dev
RUN pip install -r requirements.txt

COPY . .

# Install node dependencies
WORKDIR /usr/src/smallbrains-app/static

RUN npm install

WORKDIR /usr/src/smallbrains-app

# Configure port
EXPOSE 8000

# Run server
CMD [ "python", "/usr/src/smallbrains-app/manage.py", "runserver", "0.0.0.0:8000" ]
