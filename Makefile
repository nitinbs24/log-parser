data:
	python -m src.prepare_data --config configs/split.yaml
baselines:
	python -m src.baselines.drain_baseline
train:
	python -m src.train --config $(CONFIG)
eval:
	python -m src.evaluate --model $(MODEL) --split $(SPLIT)