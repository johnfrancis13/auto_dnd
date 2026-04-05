import base64
import io
import threading
from typing import Optional

_PIPE = None
_PIPE_LOCK = threading.Lock()


def _load_pipeline():
    import torch
    from diffusers import StableDiffusionPipeline
    from diffusers import EulerAncestralDiscreteScheduler

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(
        "Lykon/dreamshaper-7",
        torch_dtype=dtype,
    )
    pipe = pipe.to(device)

    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipe.scheduler.config
    )
    pipe.safety_checker = None
    return pipe


def _get_pipeline():
    global _PIPE
    if _PIPE is None:
        with _PIPE_LOCK:
            if _PIPE is None:
                _PIPE = _load_pipeline()
    return _PIPE


def generate_scene_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    width: int = 768,
    height: int = 512,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 30,
) -> str:
    pipe = _get_pipeline()
    result = pipe(
        prompt,
        negative_prompt=negative_prompt,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        num_images_per_prompt=1,
        height=height,
        width=width,
    )
    image = result.images[0]
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
