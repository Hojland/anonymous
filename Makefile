project=$(notdir $(shell pwd))
image_name=docker.pkg.github.com/hojland/anonymous

build_local_cpu:
	docker build -t ${image_name}:local --build-arg --build-arg PROD_ENV=$(env) \
		-f Dockerfile .

run_app:
	@docker run \
		-it \
		-d \
		--rm \
		-p 8000:8000 \
		--name $(project)-api \
		--env-file .env \
		${image_name}:local \
		"uvicorn app:app --host 0.0.0.0 --port 8000"

docker_login:
	@echo "Requesting credentials for docker login"
	@$(eval export GITHUB_ACTOR=hojland)
	@$(eval export GITHUB_TOKEN=$(shell awk -F "=" '/GITHUB_TOKEN/{print $$NF}' .env))
	@docker login https://docker.pkg.github.com/nuuday/ -u $(GITHUB_ACTOR) -p $(GITHUB_TOKEN)

init:
	poetry shell
	python3 -m spacy download da_core_news_sm