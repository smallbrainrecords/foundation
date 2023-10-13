#!/usr/bin/env zsh

version_number=$1;
environment=$2

if [ "prod" = $environment ]; then
    django_settings_module="project.settings_prod"
else
    django_settings_module="project.settings"
fi

tag_name="us-east5-docker.pkg.dev/hi-core/foundation/$environment:v"
tag_name+=$version_number
docker build -t smallbrain-django --build-arg django_settings_module=$django_settings_module .
docker tag smallbrain-django:latest $tag_name
docker push $tag_name
gcloud compute instances update-container --container-image=$tag_name smallbrain-foundation-$environment