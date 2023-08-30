#!/bin/bash

gunicorn --workers=3 --threads=2 project.wsgi:application -D
nginx -g "daemon off;"