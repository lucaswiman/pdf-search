.PHONY: build serve test test-docker clean

build:
	docker-compose build

serve:
	docker-compose up

test:
	docker-compose -f docker-compose-test.yml up --build --abort-on-container-exit --exit-code-from test
	docker-compose -f docker-compose-test.yml down -v

test-local:
	poetry run pytest

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
