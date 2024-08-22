FROM python:3.12-bookworm

ARG django_settings_module
ENV DJANGO_SETTINGS_MODULE=${django_settings_module}

RUN apt-get -y update && apt-get -y install nginx

COPY nginx.conf /etc/nginx/sites-available/default

COPY . /
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000
EXPOSE 80

RUN chmod u+x init.sh
ENTRYPOINT ["./init.sh"]
