SHELL=zsh
venv=source .venv/bin/activate &&

OPENSSL_IMAGE:=python:3.11-slim

default: .venv requirements-frozen.txt leaf_api/auth/keypair.pem docker-compose.yaml.build docker-compose.yaml.up

.venv:
	uv venv $@
	$(MAKE) .venv/lib/python/site-packages

.venv/lib/python/site-packages: requirements.txt
	$(venv) uv pip install -r requirements.txt --native-tls

requirements-frozen.txt: requirements.txt
	$(venv) uv pip freeze > $@

docker-compose.yaml.build:
	docker compose build

docker-compose.yaml.up:
	docker compose up -d
	docker compose logs -f

docker-compose.yaml.down:
	docker compose down

leaf_api/auth/keypair.pem:
	docker run --rm -it --entrypoint openssl \
		-v "$(PWD)/$(@D)/:/tmp/" \
		$(OPENSSL_IMAGE) \
		genpkey -algorithm ed25519 -outform PEM -out /tmp/$(@F)

leaf_api/auth/public_key.pem: leaf_api/auth/keypair.pem
	docker run --rm -it --entrypoint openssl \
		-v "$(PWD)/$(@D)/:/tmp/" \
		$(OPENSSL_IMAGE) \
		ec -inform PEM -in /tmp/$$(basename $<) -pubout -out /tmp/$(@F)

