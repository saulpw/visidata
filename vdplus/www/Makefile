.PHONY: run build

run: build
	docker run \
		-e GOOGLE_APPLICATION_CREDENTIALS=/creds/default_application_credentials.json \
		-v "$$HOME/.config/gcloud":/creds \
		-v "$$PWD":/etc/vd \
		-e PORT=9500 \
		-p 9500:9500 \
		--rm \
		vdwww:latest

build:
	docker build . -t vdwww:latest
