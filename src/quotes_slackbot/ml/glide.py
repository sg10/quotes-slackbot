import logging

import torch as th
from glide_text2im.clip.model_creation import create_clip_model
from glide_text2im.model_creation import (
    create_model_and_diffusion, model_and_diffusion_defaults,
    model_and_diffusion_defaults_upsampler)
from PIL import Image

from quotes_slackbot.config import config

logger = logging.getLogger(__name__)


DEBUG = True

BASE_MODEL_PATH = "models/base.pt"
UPSAMPLE_MODEL_PATH = "models/upsample.pt"
CLIP_IMAGE_ENC_MODEL_PATH = "models/clip_image_enc.pt"
CLIP_TEXT_ENC_MODEL_PATH = "models/clip_text_enc.pt"


def run_for_prompt(image_prompt: str) -> Image:
    logger.info("Initializing GLIDE")

    has_cuda = th.cuda.is_available()
    device = th.device("cpu" if not has_cuda else "cuda")

    options = model_and_diffusion_defaults()
    options["use_fp16"] = has_cuda
    options["timestep_respacing"] = str(
        config.glide_timestep_respacing
    )  # use 100 diffusion steps for fast sampling
    model, diffusion = create_model_and_diffusion(**options)
    model.eval()
    if has_cuda:
        model.convert_to_fp16()
    model.to(device)
    model.load_state_dict(th.load(BASE_MODEL_PATH, device))
    logger.info(
        "total base parameters {0}".format(sum(x.numel() for x in model.parameters()))
    )

    options_up = model_and_diffusion_defaults_upsampler()
    options_up["use_fp16"] = has_cuda
    options_up[
        "timestep_respacing"
    ] = config.upsampling_respacing  # use 27 diffusion steps for very fast sampling
    model_up, diffusion_up = create_model_and_diffusion(**options_up)
    model_up.eval()
    if has_cuda:
        model_up.convert_to_fp16()
    model_up.to(device)
    model_up.load_state_dict(th.load(UPSAMPLE_MODEL_PATH, device))
    logger.info(
        "total upsampler parameters {0}".format(
            sum(x.numel() for x in model_up.parameters())
        )
    )

    clip_model = create_clip_model(device=device)
    clip_model.image_encoder.load_state_dict(th.load(CLIP_IMAGE_ENC_MODEL_PATH, device))
    clip_model.text_encoder.load_state_dict(th.load(CLIP_TEXT_ENC_MODEL_PATH, device))

    # Sampling parameters
    batch_size = 1

    # Tune this parameter to control the sharpness of 256x256 images.
    # A value of 1.0 is sharper, but sometimes results in grainy artifacts.
    upsample_temp = 0.997

    # Create the text tokens to feed to the model.
    tokens = model.tokenizer.encode(image_prompt)
    tokens, mask = model.tokenizer.padded_tokens_and_mask(tokens, options["text_ctx"])

    # Pack the tokens together into model kwargs.
    model_kwargs = dict(
        tokens=th.tensor([tokens] * batch_size, device=device),
        mask=th.tensor([mask] * batch_size, dtype=th.bool, device=device),
    )

    # Setup guidance function for CLIP model.
    cond_fn = clip_model.cond_fn(
        [image_prompt] * batch_size, config.glide_guidance_scale
    )

    logger.info("Generating image")

    model.del_cache()
    samples = diffusion.p_sample_loop(
        model,
        (batch_size, 3, options["image_size"], options["image_size"]),
        device=device,
        clip_denoised=True,
        progress=True,
        model_kwargs=model_kwargs,
        cond_fn=cond_fn,
    )
    model.del_cache()

    tokens = model_up.tokenizer.encode(image_prompt)
    tokens, mask = model_up.tokenizer.padded_tokens_and_mask(
        tokens, options_up["text_ctx"]
    )

    # Create the model conditioning dict.
    model_kwargs = dict(
        # Low-res image to upsample.
        low_res=((samples + 1) * 127.5).round() / 127.5 - 1,
        # Text tokens
        tokens=th.tensor([tokens] * batch_size, device=device),
        mask=th.tensor(
            [mask] * batch_size,
            dtype=th.bool,
            device=device,
        ),
    )

    logger.info("Upsampling")

    model_up.del_cache()
    up_shape = (batch_size, 3, options_up["image_size"], options_up["image_size"])
    up_samples = diffusion_up.ddim_sample_loop(
        model_up,
        up_shape,
        noise=th.randn(up_shape, device=device) * upsample_temp,
        device=device,
        clip_denoised=True,
        progress=True,
        model_kwargs=model_kwargs,
        cond_fn=None,
    )[:batch_size]
    model_up.del_cache()

    def to_pil(batch: th.Tensor):
        """Display a batch of images inline."""
        scaled = ((batch + 1) * 127.5).round().clamp(0, 255).to(th.uint8).cpu()
        reshaped = scaled.permute(2, 0, 3, 1).reshape([batch.shape[2], -1, 3])
        return Image.fromarray(reshaped.numpy())

    return to_pil(up_samples)
