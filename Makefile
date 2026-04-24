OPENSSL_IMAGE:=docker.io/library/python:3.11-slim

default: leaf_api/auth/keypair.pem

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

