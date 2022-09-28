FROM nikolaik/python-nodejs:python3.7-nodejs18-alpine

# Set environment variables
ENV DATABASE_NAME=smallbrains_development
ENV DATABASE_TEST_NAME=smallbrains_test
ENV DATABASE_NAME_SNOMEDCT=snomedct
ENV DATABASE_USER=root
ENV DATABASE_PASSWORD=root
ENV DATABASE_HOST=172.17.0.1
ENV DATABASE_PORT=3306
ENV SECRET_KEY=secret

WORKDIR /usr/src/smallbrains-app

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# runtime dependencies
RUN set -eux; \
  apk add --no-cache \
  ca-certificates \
  tzdata \
  ;

ENV GPG_KEY 0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D
ENV PYTHON_VERSION 3.7.13

RUN set -eux; \
  \
  apk add --no-cache --virtual .build-deps \
  gnupg \
  tar \
  xz \
  \
  bluez-dev \
  bzip2-dev \
  dpkg-dev dpkg \
  expat-dev \
  findutils \
  gcc \
  gdbm-dev \
  libc-dev \
  libffi-dev \
  libnsl-dev \
  libtirpc-dev \
  linux-headers \
  make \
  ncurses-dev \
  openssl-dev \
  pax-utils \
  readline-dev \
  sqlite-dev \
  tcl-dev \
  tk \
  tk-dev \
  util-linux-dev \
  xz-dev \
  zlib-dev \
  ;

RUN pip install setuptools==45

# Install mysql client
RUN apk add --update-cache \
  gcc \
  build-base \
  curl \
  git \
  jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
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
CMD [ "python", "/usr/src/smallbrains-app/manage.py", "runserver", "0.0.0.0:8000" ]