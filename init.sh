#!/bin/bash

gunicorn --workers=4 --threads=2 --bind=unix:/gunicorn.sock project.wsgi:application -D
nginx -g "daemon off;"