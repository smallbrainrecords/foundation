#!/bin/bash

gunicorn --workers=3 --worker-class=gevent --worker-connections=1000 project.wsgi:application -D
nginx -g "daemon off;"