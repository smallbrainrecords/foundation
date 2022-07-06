FROM node:lts-alpine

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
  ; \
  \
  wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz"; \
  wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc"; \
  GNUPGHOME="$(mktemp -d)"; export GNUPGHOME; \
  gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$GPG_KEY"; \
  gpg --batch --verify python.tar.xz.asc python.tar.xz; \
  command -v gpgconf > /dev/null && gpgconf --kill all || :; \
  rm -rf "$GNUPGHOME" python.tar.xz.asc; \
  mkdir -p /usr/src/python; \
  tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz; \
  rm python.tar.xz; \
  \
  cd /usr/src/python; \
  gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)"; \
  ./configure \
  --build="$gnuArch" \
  --enable-loadable-sqlite-extensions \
  --enable-optimizations \
  --enable-option-checking=fatal \
  --enable-shared \
  --with-system-expat \
  --without-ensurepip \
  ; \
  nproc="$(nproc)"; \
  make -j "$nproc" \
  # set thread stack size to 1MB so we don't segfault before we hit sys.getrecursionlimit()
  # https://github.com/alpinelinux/aports/commit/2026e1259422d4e0cf92391ca2d3844356c649d0
  EXTRA_CFLAGS="-DTHREAD_STACK_SIZE=0x100000" \
  LDFLAGS="-Wl,--strip-all" \
  # setting PROFILE_TASK makes "--enable-optimizations" reasonable: https://bugs.python.org/issue36044 / https://github.com/docker-library/python/issues/160#issuecomment-509426916
  PROFILE_TASK='-m test.regrtest --pgo \
  test_array \
  test_base64 \
  test_binascii \
  test_binhex \
  test_binop \
  test_bytes \
  test_c_locale_coercion \
  test_class \
  test_cmath \
  test_codecs \
  test_compile \
  test_complex \
  test_csv \
  test_decimal \
  test_dict \
  test_float \
  test_fstring \
  test_hashlib \
  test_io \
  test_iter \
  test_json \
  test_long \
  test_math \
  test_memoryview \
  test_pickle \
  test_re \
  test_set \
  test_slice \
  test_struct \
  test_threading \
  test_time \
  test_traceback \
  test_unicode \
  ' \
  ; \
  make install; \
  \
  cd /; \
  rm -rf /usr/src/python; \
  \
  find /usr/local -depth \
  \( \
  \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
  -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
  -o \( -type f -a -name 'wininst-*.exe' \) \
  \) -exec rm -rf '{}' + \
  ; \
  \
  find /usr/local -type f -executable -not \( -name '*tkinter*' \) -exec scanelf --needed --nobanner --format '%n#p' '{}' ';' \
  | tr ',' '\n' \
  | sort -u \
  | awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }' \
  | xargs -rt apk add --no-network --virtual .python-rundeps \
  ; \
  apk del --no-network .build-deps; \
  \
  python3 --version

# make some useful symlinks that are expected to exist ("/usr/local/bin/python" and friends)
RUN set -eux; \
  for src in idle3 pydoc3 python3 python3-config; do \
  dst="$(echo "$src" | tr -d 3)"; \
  [ -s "/usr/local/bin/$src" ]; \
  [ ! -e "/usr/local/bin/$dst" ]; \
  ln -svT "$src" "/usr/local/bin/$dst"; \
  done

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 22.0.4
# https://github.com/docker-library/python/issues/365
ENV PYTHON_SETUPTOOLS_VERSION 45
# https://github.com/pypa/get-pip
ENV PYTHON_GET_PIP_URL https://github.com/pypa/get-pip/raw/6ce3639da143c5d79b44f94b04080abf2531fd6e/public/get-pip.py
ENV PYTHON_GET_PIP_SHA256 ba3ab8267d91fd41c58dbce08f76db99f747f716d85ce1865813842bb035524d

RUN set -eux; \
  \
  wget -O get-pip.py "$PYTHON_GET_PIP_URL"; \
  echo "$PYTHON_GET_PIP_SHA256 *get-pip.py" | sha256sum -c -; \
  \
  export PYTHONDONTWRITEBYTECODE=1; \
  \
  python get-pip.py \
  --disable-pip-version-check \
  --no-cache-dir \
  --no-compile \
  "pip==$PYTHON_PIP_VERSION" \
  "setuptools==$PYTHON_SETUPTOOLS_VERSION" \
  ; \
  rm -f get-pip.py; \
  \
  pip --version



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