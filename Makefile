# VE mapping
VE_NODE_NUMBER?=1
VENODEID=${VE_NODE_NUMBER}
VE=$(shell readlink -f /dev/veslot${VENODEID})

# Base img properties
BASEIMG_NAME?=centos
BASEIMG_VERSION?=8.3.2011
NEC_TOOLS_VERSION?=2.3-1

# Docker image properties
IMAGE_NAME=vebox
VERSION_TAG=develop
VEBOX_CONTAINER=vebox

BASE_PATH=${PWD}/ve-base-dev-docker

all: build_context build_image run_image

build_context:
	rm -rf context/
	mkdir -p context
	python3 ve-box.py ${BASEIMG_NAME} ${BASEIMG_VERSION} ${NEC_TOOLS_VERSION}
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
	echo "Device ${VE}"
	docker run \
		-v /dev:/dev:z \
	        --device ${VE}:${VE} \
	        -v /var/opt/nec/ve/veos:/var/opt/nec/ve/veos:z \
	        -v ${HOME}:${HOME}:z \
	        -v /etc/group:/etc/group:ro \
	        -v /etc/passwd:/etc/passwd:ro \
		-u $(shell id -u):$(shell id -g) \
		-w ${PWD} \
		--rm -it \
		--network host \
		--name ${VEBOX_CONTAINER} \
		--mount type=bind,source=${PWD}/workdir,target=/opt/workdir \
		${IMAGE_NAME}:latest \
		/bin/bash
help:
	cat Makefile

