SRC_DIR = ./montmark
TST_DIR = ./tests
SPEC = $(TST_DIR)/spec.json


$(SPEC):
	wget -P $(TST_DIR) https://spec.commonmark.org/0.31.2/spec.json

cmark: $(SPEC)
	PYTHONPATH=. python3 tests/cmark.py

test:
	python3 -m unittest tests/test.py -v

d:
	DEBUG=1 python3 -i debug.py

clean:
	rm $(SPEC)
	rm -rf ./__pycache__
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(TST_DIR)/__pycache__


