# food

- `core` never imports `connectors`; only the CLIs (`restock.py`, `predictor.py`) wire the two together.
- Import as `food.core…` / `food.connectors…` and run the CLIs from the repo root as `python3 -m food.restock` / `python3 -m food.predictor`.
