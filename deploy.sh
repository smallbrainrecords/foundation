#!/usr/bin/env zsh

version_number=$1;
environment=$2
tag_name="us-east5-docker.pkg.dev/hi-core/foundation/development:v"
tag_name+=$version_number
docker build -t smallbrain-django .
docker tag smallbrain-django:latest $tag_name
docker push $tag_name
gcloud compute instances update-container --container-image=$tag_name smallbrain-foundation-$environment