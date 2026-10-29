"""Cached ViT inference with an explicitly labeled offline demo fallback."""
import time
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from .config import MODEL_NAME

class ViTClassifier:
    def __init__(self, model_name=MODEL_NAME): self.model_name=model_name; self._model=None; self._processor=None; self._torch=None
    def load_model(self):
        if self._model is not None: return
        try:
            import torch
            from transformers import ViTForImageClassification, ViTImageProcessor
            self._torch=torch; self._processor=ViTImageProcessor.from_pretrained(self.model_name); self._model=ViTForImageClassification.from_pretrained(self.model_name); self._model.eval()
        except Exception as exc: raise RuntimeError(f"Could not load ViT model '{self.model_name}'. Check transformers/PyTorch and model access. Details: {exc}") from exc
    def preprocess_image(self,path):
        try:
            image=Image.open(path).convert("RGB"); dims=image.size
            return image,dims
        except (OSError,UnidentifiedImageError) as exc: raise ValueError("Choose a valid JPG, PNG, or WEBP image.") from exc
    def predict_top_k(self,path,k=5,demo=False):
        image,dims=self.preprocess_image(path); started=time.perf_counter()
        if demo:
            # Deterministic mock prediction. No claim of model inference in Demo Mode.
            import hashlib
            labels=["Jacket","Dress","Shirt","Trousers","Skirt","Knitwear","Coat","Bag"]
            seed=int(hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8],16); order=sorted(labels,key=lambda x:hashlib.sha256(f"{seed}{x}".encode()).hexdigest()); vals=[max(2,86-i*17) for i in range(min(k,len(order)))]; total=sum(vals)
            return {"predictions":[(order[i],vals[i]/total) for i in range(len(vals))],"dimensions":dims,"elapsed":time.perf_counter()-started,"model":"Demo classifier (mock)","timestamp":time.strftime("%Y-%m-%d %H:%M:%S"),"demo":True}
        self.load_model(); inputs=self._processor(images=image,return_tensors="pt")
        with self._torch.inference_mode(): logits=self._model(**inputs).logits[0]; probs=self._torch.softmax(logits,dim=-1); scores,indices=self._torch.topk(probs,min(k,probs.numel()))
        labels=self._model.config.id2label
        return {"predictions":[(labels[int(i)],float(v)) for v,i in zip(scores,indices)],"dimensions":dims,"elapsed":time.perf_counter()-started,"model":self.model_name,"timestamp":time.strftime("%Y-%m-%d %H:%M:%S"),"demo":False}
