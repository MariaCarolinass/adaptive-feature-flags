import joblib
import pandas as pd


class ModelPredictor:
    def __init__(self, model_path: str) -> None:
        artifact = joblib.load(model_path)
        self.model = artifact["model"] if isinstance(artifact, dict) and "model" in artifact else artifact

    def predict_score(self, payload: dict) -> float:
        row = pd.DataFrame([payload])
        return float(self.model.predict_proba(row)[0][1])