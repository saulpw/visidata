.PHONY: run build push deploy

run: build
	docker run -v "$$PWD":/etc/vd -e ORT=9500 -p 9500:9500 --rm vdwww:latest

build:
	docker build . -t vdwww:latest -t gcr.io/psp-sandbox/vdwww

push: build
	docker push gcr.io/psp-sandbox/vdwww

deploy: push
	gcloud run deploy vdemo --image gcr.io/psp-sandbox/vdwww --region us-central1
