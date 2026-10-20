data:
	python -m src.prepare_data --config configs/split.yaml
baselines:
	python -m src.baselines.drain_baseline
train:
	python -m src.train --config $(CONFIG)
eval:
	python -m src.evaluate --model $(MODEL) --split $(SPLIT)
base-baselines:
	for s in test_heldout test_template_disjoint handcrafted; do \
	  for m in "base_zeroshot 0" "base_fewshot 5"; do set -- $$m; \
	    python -m src.predict --split $$s --backend unsloth --shots $$2 --out results/$$1/$$s.csv && \
	    python -m src.evaluate --pred results/$$1/$$s.csv --out results/$$1/$$s.json || exit 1; \
	  done; \
	done
