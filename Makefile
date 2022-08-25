pytest:
	poetry run python -m unittest test/*__test.py

format:
	poetry run pre-commit run --all-files

only_test:
	poetry run python -m unittest test/0$(N)__test.py

algo_test:
	poetry run python -m unittest test/0{3,4}__test.py
