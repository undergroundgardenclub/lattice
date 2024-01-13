import numpy as np
from typing import List
import torch
from transformers import CLIPProcessor, CLIPModel


# SETUP
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# ENCODINGS
def clip_encode(images: List = [], text: List = []):
    print(f"[clip_encode] {len(images)} images, {len(text)} text")
    image_outputs = None
    text_outputs = None
    # process
    with torch.no_grad():
        # --- images
        if images is not None and len(images) > 0:
            # process inputs (do I need to transform images? Or can I pass in if they're PNGs aka video frames from CV2) -> embeddings
            image_inputs = processor(images=images, return_tensors="pt", padding=True)
            image_outputs = model.get_image_features(**image_inputs)
        # --- text
        if text is not None and len(text) > 0:
            # process inputs -> embeddings
            text_shortened = list(map(lambda t: t[:140], text)) # 77 token limit
            text_inputs = processor(text=text_shortened, return_tensors="pt", padding=True)
            text_outputs = model.get_text_features(**text_inputs)
    # return embeddings
    return image_outputs, text_outputs


# CALCS
def clip_similarity(features_list, feature_compared) -> np.ndarray:
    print(f"[clip_similarity] {len(features_list)} features")
    # Ensure feature_compared is two-dimensional for matrix multiplication
    feature_compared = feature_compared.unsqueeze(0) if feature_compared.dim() == 1 else feature_compared
    # Normalize the features
    features_list = features_list / features_list.norm(dim=-1, keepdim=True)
    feature_compared = feature_compared / feature_compared.norm(dim=-1, keepdim=True)
    # Calculate cosine similarity
    similarity = torch.matmul(features_list, feature_compared.T).squeeze()
    # return results list
    similarity_arr = similarity.cpu().numpy()
    return similarity_arr if similarity_arr.ndim > 0 else np.array([similarity_arr])
