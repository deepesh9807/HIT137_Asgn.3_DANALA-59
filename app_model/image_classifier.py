from transformers import pipeline
from PIL import Image
from helpers.decorators import log_action, timeit
from app_model.base import BaseModelAdapter

class ImageClassifierAdapter(BaseModelAdapter):
    model_name = "google/vit-base-patch16-224"
    category = "Image Classification"
    description = "Classifies an image with ViT."

    def load(self):
        self._pipe = pipeline("image-classification", model=self.model_name)

    @log_action
    @timeit
    def run(self, payload):
        # payload may be a raw path string or a UI dict
        if isinstance(payload, dict):
            path = (payload.get("image_path") or payload.get("prompt") or "").strip()
        else:
            path = (payload or "").strip()
        if not path:
            return {"result":"Choose an image file first."}
        img = Image.open(path).convert("RGB")
        pred = self._pipe(img)[0]
        return {"result": f"{pred['label']} ({pred['score']:.2f})", "image_path": path}
