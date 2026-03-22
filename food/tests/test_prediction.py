from food.core.prediction import Prediction


def test_handoff_round_trips_in_order(tmp_path):
    """What predictor writes is exactly what push reads back, ranking order kept."""
    preds = [Prediction("milk", 0.9), Prediction("bread", 0.25), Prediction("eggs", 0.5)]
    path = str(tmp_path / "predict.yaml")

    Prediction.write_handoff(preds, path)

    assert Prediction.read_handoff(path) == preds


def test_empty_handoff_reads_as_empty_list(tmp_path):
    """An empty prediction list survives the file, so push can say there is nothing to do."""
    path = str(tmp_path / "predict.yaml")

    Prediction.write_handoff([], path)

    assert Prediction.read_handoff(path) == []
