FROM node:lts-alpine

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
RUN apk update && apk upgrade && apk add --update-cache \
  python3 \
  python3-dev \
  build-base \
  curl \
  git \
  && ln -sf python3 /usr/bin/python \
  && python3 -m ensurepip \
  && pip3 install --no-cache --upgrade pip setuptools==45 \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/*

# Install mysql client
RUN apk add --update-cache \
  mariadb-dev \
  postgresql-dev \
  libxml2-dev \
  libxslt-dev \
  openldap-dev\
  libffi-dev

# Install python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Install node dependencies
WORKDIR /usr/src/smallbrains-app/static

RUN npm install

WORKDIR /usr/src/smallbrains-app

# Configure port
EXPOSE 8000

# Run server
CMD [ "python", "/usr/src/smallbrains-app/manage.py", "runserver", "0.0.0.0:8000", "--noreload" ]