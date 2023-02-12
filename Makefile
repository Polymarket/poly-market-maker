init:
	./install-dev.sh

test:
	pytest -s

fmt:
	black ./.