import torch

from app.ai.model_loader import load_model
from app.ai.preprocess import preprocess_image


@torch.no_grad()
def infer_erosion(image_path: str) -> dict:
    loaded = load_model()
    config = loaded.config

    threshold = float(config.get("threshold", 0.314))
    mean = config.get("train_mean", [0.0, 0.0, 0.0])
    std = config.get("train_std", [1.0, 1.0, 1.0])

    x, preprocess_meta = preprocess_image(image_path, mean=mean, std=std)
    x = x.to("cpu")

    logits = loaded.model(x)
    probability = torch.sigmoid(logits).item()
    predicted_class = 1 if probability >= threshold else 0

    return {
        "probability": float(probability),
        "predicted_class": int(predicted_class),
        "threshold": float(threshold),
        "model_version": str(config.get("model_version", "EROBinaryResNet18")),
        "preprocess": preprocess_meta,
    }