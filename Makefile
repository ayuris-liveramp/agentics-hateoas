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

docker-compose.yaml.build: requirements-frozen.txt
	docker compose build

docker-compose.yaml.up:
	docker compose up

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

leaf_api/auth/token.b64: leaf_api/auth/token.admin.b64

leaf_api/auth/token.%.b64: leaf_api/auth/public_key.pem
	python -m leaf_api.auth.token $* > $@

.PHONY: test
test:
	@echo "Checking docker compose services..."
	@docker compose ps --services | grep -q leaf-api && docker compose ps --services | grep -q root-app || \
		(echo "Error: docker compose services not running. Run 'make' first."; exit 1)
	@echo "Building test image..."
	@docker build -f tests/Dockerfile -t agentics-test .
	@echo "Running functional tests..."
	@docker run --rm \
		--network agentics-network \
		-v "$(PWD)/tests:/app/tests" \
		-e LEAF_API_URL=http://leaf-api:5000 \
		-e ROOT_APP_URL=http://root-app:5001 \
		agentics-test pytest -v /app/tests
