#!/bin/bash

gunicorn project.wsgi:application -D
nginx -g "daemon off;"