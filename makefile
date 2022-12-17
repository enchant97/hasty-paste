none:

docker-build:
	@docker build -t hasty-paste .

py-venv:
	@python -m venv .venv

py-install:
	@python -m pip install .
