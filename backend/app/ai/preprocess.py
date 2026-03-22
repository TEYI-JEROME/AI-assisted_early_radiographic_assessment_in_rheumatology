from PIL import Image
from torchvision import transforms


def preprocess_image(image_path: str, *, mean: list[float], std: list[float]):
    image = Image.open(image_path)
    image = image.convert("L").convert("RGB")

    tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )

    x = tf(image).unsqueeze(0)
    meta = {
        "conversion": "L->RGB",
        "resize": [224, 224],
    }
    return x, meta