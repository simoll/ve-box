IMAGE_NAME=vebox
VERSION_TAG=develop
VEBOX_CONTAINER=vebox

BASE_PATH=${PWD}/ve-base-dev-docker

all: build_context build_image run_image

build_context:
	rm -rf context/
	mkdir -p context
	python3 ve-box.py
	cp ${BASE_PATH}/dnf.conf context/
	cp ${BASE_PATH}/TSUBASA-repo.repo context/
	cp ${BASE_PATH}/CentOS-Base.repo context/
	cp ${BASE_PATH}/CentOS-Extras.repo context/
	cp ${BASE_PATH}/CentOS-AppStream.repo context/

build_image:
	cd context && docker build \
		--network host \
		--tag ${IMAGE_NAME}:${VERSION_TAG} \
		--build-arg host_proxy=${http_proxy} \
		.
	cd context && docker image tag ${IMAGE_NAME}:${VERSION_TAG} ${IMAGE_NAME}:latest

run_image:
	docker run \
		--rm -it \
		--network host \
		--name ${VEBOX_CONTAINER} \
		--mount type=bind,source=${PWD}/workdir,target=/opt/workdir \
		${IMAGE_NAME}:latest \
		/bin/bash
help:
	cat Makefile

