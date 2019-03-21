.PHONY = install

install:
	virtualenv ENV
	source ENV/bin/activate && pip install -r requirements.txt
	which npm && which node && npm i || echo "Node not found, discord unavailable"
