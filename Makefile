
install:
	@python setup.py install
	@make clean

test:

clean:
	@rm -fr dist build *.egg-info *.py[cod]

upload:
	@python setup.py sdist upload -r pypi
	@make clean

.PHONY: install test clean upload
