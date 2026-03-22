import sys

import pytest

from food import predictor
from food.core import history
from food.core.prediction import Prediction

_DB_ROWS = [
    ("milk", "2026-01-01", True), ("bread", "2026-01-01", True), ("eggs", "2026-01-01", False),
    ("milk", "2026-01-08", True), ("bread", "2026-01-08", False), ("eggs", "2026-01-08", True),
    ("milk", "2026-01-15", True), ("bread", "2026-01-15", True), ("eggs", "2026-01-15", True),
    ("milk", "2026-01-22", False), ("bread", "2026-01-22", True), ("eggs", "2026-01-22", False),
]


def _run(monkeypatch, *args):
    """Invoke the CLI as `predictor.py <args>`, so tests drive the real entry point."""
    argv = ["predictor.py", *args]
    monkeypatch.setattr(sys, "argv", argv)
    predictor.main()


@pytest.fixture(autouse=True)
def seed_history(workspace):
    """Seed a four-commit history in the redirected workspace so the predictor runs offline."""
    history.append([(item, day, need) for item, day, need in _DB_ROWS])
    return workspace


def test_main_hands_off_active_items_ranked(monkeypatch, write_items):
    """The handoff holds every active item and no inactive one, most likely first."""
    write_items(["milk", "bread"], inactive=["eggs"])

    _run(monkeypatch)

    preds = Prediction.read_handoff()
    assert {p.item for p in preds} == {"milk", "bread"}
    assert [p.prob for p in preds] == sorted((p.prob for p in preds), reverse=True)


def test_main_top_n_limits_handoff(monkeypatch, write_items):
    """--top-n caps the handoff at the N most likely items."""
    write_items(["milk", "bread", "eggs"])

    _run(monkeypatch, "--top-n", "2")

    assert len(Prediction.read_handoff()) == 2
