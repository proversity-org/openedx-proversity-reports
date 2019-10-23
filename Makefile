###############################################
#
# openedx-proversity-reports commands.
#
###############################################

.DEFAULT_GOAL := help

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## delete most git-ignored files
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +

requirements-ginkgo: ## install environment requirements
	pip install -r requirements/ginkgo.txt

requirements-hawthorn: ## install environment requirements
	pip install -r requirements/hawthorn.txt

requirements-ironwood: ## install environment requirements
	pip install -r requirements/ironwood.txt

run-quality-test: clean ## Run quality test.
	pylint ./openedx_proversity_reports --rcfile=./setup.cfg

# TODO Fix this command.
upgrade: clean ## Update requirements.txt file.
	pip-compile --output-file requirements.txt requirements.in
