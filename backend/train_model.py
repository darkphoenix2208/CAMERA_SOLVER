import joblib
from digit_ml import _build_training_data
import numpy as np

try:
    from sklearn.neural_network import MLPClassifier
    rng = np.random.default_rng(42)
    X, y = _build_training_data(rng)
    _clf = MLPClassifier(
        hidden_layer_sizes=(256, 128),
        max_iter=800,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15,
    )
    _clf.fit(X, y)
    joblib.dump(_clf, "digit_model.pkl")
    print("Model saved to digit_model.pkl")
except Exception as e:
    print(f"Error: {e}")
