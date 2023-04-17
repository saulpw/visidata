.PHONY: run build push deploy

run: build
	docker run -e PORT=9500 -p 9500:9500 --rm vdwww:latest

build:
	# TODO(cpcloud): remove --no-cache if we ever get off of HEAD of the things
	docker build --no-cache --rm . -t vdwww:latest -t gcr.io/psp-sandbox/vdwww

push: build
	docker push gcr.io/psp-sandbox/vdwww

deploy: push
	gcloud run deploy vdemo --image gcr.io/psp-sandbox/vdwww --region us-central1
