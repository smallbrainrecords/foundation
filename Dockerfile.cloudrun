FROM python:3.12-bookworm

ENV DJANGO_SETTINGS_MODULE=project.settings
ENV PYTHONUNBUFFERED=1

RUN apt-get -y update && apt-get -y install default-libmysqlclient-dev pkg-config build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

RUN chmod u+x init-cloudrun.sh
ENTRYPOINT ["/app/init-cloudrun.sh"]
