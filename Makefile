install:
	conda env update --file environment.yml --prune

run:
	python server.py

hotfix:
	git add . && git commit -m "Hotfix" && git push production main:master
