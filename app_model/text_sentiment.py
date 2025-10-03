from transformers import pipeline
from helpers.decorators import log_action, timeit
from app_model.base import BaseModelAdapter

class TextSentimentAdapter(BaseModelAdapter):
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    category = "Text Classification"
    description = "Sentiment (positive/negative) using DistilBERT."

    def load(self):
        self._pipe = pipeline("sentiment-analysis", model=self.model_name)

    @log_action
    @timeit
    def run(self, payload):
        text = (payload or "").strip()
        if not text:
            return {"result": "Enter text in the box."}
        out = self._pipe(text)[0]
        return {"result": f"{out['label']} ({out['score']:.2f})"}
