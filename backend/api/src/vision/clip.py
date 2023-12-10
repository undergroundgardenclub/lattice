from typing import List
import torch
from transformers import CLIPProcessor, CLIPModel


# SETUP
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# ENCODINGS
def clip_encode(images: List, text: List):
    print(f"[clip_encode] {len(images)} images, {len(text)} text")
    # process
    with torch.no_grad():
        # --- images
        if images is not None:
            # process inputs (do I need to transform images? Or can I pass in if they're PNGs aka video frames from CV2) -> embeddings
            image_inputs = processor(images=images, return_tensors="pt", padding=True)
            image_outputs = model.get_image_features(**image_inputs)
        # --- text
        if text is not None:
            # process inputs -> embeddings
            text_inputs = processor(text=text, return_tensors="pt", padding=True)
            text_outputs = model.get_text_features(**text_inputs)
        # return embeddings
        return image_outputs, text_outputs


# CALCS
def clip_similarity(features_list, feature_compared):
    print(f"[clip_similarity] {len(features_list)} features")
    # Ensure feature_compared is two-dimensional for matrix multiplication
    feature_compared = feature_compared.unsqueeze(0) if feature_compared.dim() == 1 else feature_compared
    # Normalize the features
    features_list = features_list / features_list.norm(dim=-1, keepdim=True)
    feature_compared = feature_compared / feature_compared.norm(dim=-1, keepdim=True)
    # Calculate cosine similarity
    similarity = torch.matmul(features_list, feature_compared.T).squeeze()
    # return results list
    return similarity.cpu().numpy()
