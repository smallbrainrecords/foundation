#!/bin/bash

gunicorn --workers=8 --threads=4 --bind=unix:/gunicorn.sock project.wsgi:application -D
nginx -g "daemon off;"