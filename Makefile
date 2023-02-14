install:
	./install-dev.sh

test:
	pytest

fmt:
	black .