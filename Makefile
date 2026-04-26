SHELL=zsh
venv=source .venv/bin/activate &&

OPENSSL_IMAGE:=python:3.11-slim

default: .venv requirements-frozen.txt leaf_api/auth/keypair.pem docker-compose.yaml.build db_init/00_create_database.sql docker-compose.yaml.up

.venv:
	uv venv $@
	$(MAKE) .venv/lib/python/site-packages

.venv/lib/python/site-packages: requirements.txt
	$(venv) uv pip install -r requirements.txt --native-tls

requirements-frozen.txt: requirements.txt
	$(venv) uv pip freeze > $@

docker-compose.yaml.build: requirements-frozen.txt
	docker compose build

docker-compose.yaml.up: docker-compose.yaml.down
	docker compose up

docker-compose.yaml.down:
	-docker compose down

docker-compose.yaml.check:
	@echo "Checking docker compose services..."
	@docker compose ps --format '{{index .Labels "com.docker.compose.service"}}' | \
		wc -l | xargs -I{} test {} -eq 3 || \
		(echo "Error: docker compose services not running. Run 'make' first."; exit 1)

psql: docker-compose.yaml.check
	docker compose exec postgres psql -U agentics_user -p 5432 agentics_db

db_init/00_create_database.sql: leaf_api/models/*.py
	docker run --rm -it --entrypoint python \
		-v "$(PWD)/scripts/:/app/scripts/" \
		localhost/agentics-hateoas_leaf-api \
		/app/scripts/generate_db_sql.py | tr -d '$$\r' > $@

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
test: docker-compose.yaml.check
	@echo "Building test image..."
	@docker build -f tests/Dockerfile -t agentics-test .
	@echo "Running functional tests..."
	@docker run --rm \
		--network agentics-hateoas_agentics-network \
		-v "$(PWD)/tests:/app/tests" \
		-e LEAF_API_URL=http://leaf-api:5000 \
		-e ROOT_APP_URL=http://root-app:5001 \
		agentics-test -v /app/tests
