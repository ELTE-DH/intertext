#!/bin/sh
IMAGE=yarn:latest
# Download dependencies
docker run --rm -it --user="$(id -u):$(id -g)" --env HOME=/tmp -v "$PWD":/workdir "$IMAGE" "$@" yarn
# Build the program
docker run --rm -it --user="$(id -u):$(id -g)" --env HOME=/tmp -v "$PWD":/workdir "$IMAGE" "$@" yarn build
