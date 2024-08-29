install:
	conda env update --file environment.yml --prune

run:
	python server.py
