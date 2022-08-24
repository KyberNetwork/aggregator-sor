pytest:
	poetry run python -m unittest test/*__test.py

format:
	poetry run pre-commit run --all-files
