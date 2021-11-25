IMAGE_NAME=vebox
VERSION_TAG=develop

build:
	cd context && docker build \
		--network host \
		--tag ${IMAGE_NAME}:${VERSION_TAG} \
		--build-arg host_proxy=${http_proxy} \
		.
	cd context && docker image tag ${IMAGE_NAME}:${VERSION_TAG} ${IMAGE_NAME}:latest

run:
	docker run \
		 --rm -it \
		--network host \
		--name llvm-container \
		--mount type=bind,source=${PWD}/workdir,target=/opt/workdir \
		${IMAGE_NAME}:latest \
		scl enable gcc-toolset-10 /bin/bash
