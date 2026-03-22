import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from app.ai.model_arch import EROBinaryResNet18
from app.core.config import settings
from app.core.errors import AppError


@dataclass
class LoadedModel:
    model: Any
    config: dict


_cached: LoadedModel | None = None


def _artifact_path(filename: str) -> Path:
    base = settings.resolve_path(settings.model_artifacts_dir)
    return (base / filename).resolve()


def load_model() -> LoadedModel:
    global _cached

    if _cached is not None:
        return _cached

    config_path = _artifact_path("ero_resnet18_config.json")
    checkpoint_path = _artifact_path("ero_resnet18_checkpoint.pth")
    scripted_path = _artifact_path("ero_resnet18_scripted.pt")

    if not config_path.exists():
        raise AppError("Model config file is missing.", code="model_config_missing", http_status=500)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    device = torch.device("cpu")

    use_torchscript = scripted_path.exists() and config.get("use_torchscript", False)

    if use_torchscript:
        model = torch.jit.load(str(scripted_path), map_location=device)
        model.eval()
        _cached = LoadedModel(model=model, config=config)
        return _cached

    if not checkpoint_path.exists():
        raise AppError("Model checkpoint file is missing.", code="model_checkpoint_missing", http_status=500)

    checkpoint = torch.load(str(checkpoint_path), map_location=device)

    dropout = float(checkpoint.get("dropout", 0.6))
    model = EROBinaryResNet18(dropout=dropout)

    state_dict = checkpoint.get("state_dict")
    if not state_dict:
        raise AppError("Checkpoint does not contain state_dict.", code="invalid_checkpoint", http_status=500)

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    merged_config = dict(config)
    merged_config["threshold"] = float(checkpoint.get("threshold", config.get("threshold", 0.314)))
    merged_config["train_mean"] = checkpoint.get("train_mean", config.get("train_mean", [0.0, 0.0, 0.0]))
    merged_config["train_std"] = checkpoint.get("train_std", config.get("train_std", [1.0, 1.0, 1.0]))
    merged_config["model_version"] = checkpoint.get("model_class", config.get("model_class", "EROBinaryResNet18"))

    _cached = LoadedModel(model=model, config=merged_config)
    return _cached