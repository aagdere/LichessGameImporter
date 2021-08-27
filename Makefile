clean:
	rm -rf ./pyenv

pyenv:
	python3 -m venv pyenv

install:
	. ./pyenv/bin/activate && pip3 install -r requirements.txt;	

run:
	. ./pyenv/bin/activate && python3 ChessGameImporter.py;