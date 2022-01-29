#!/bin/bash


# sudo apt install liblzma-dev

mkdir -p models

# GLIDE models, downloaded upfront for docker caching
curl -C - https://openaipublic.blob.core.windows.net/diffusion/dec-2021/base.pt --output models/base.pt
curl -C - https://openaipublic.blob.core.windows.net/diffusion/dec-2021/upsample.pt --output models/upsample.pt
curl -C - https://openaipublic.blob.core.windows.net/diffusion/dec-2021/clip_image_enc.pt --output models/clip_image_enc.pt
curl -C - https://openaipublic.blob.core.windows.net/diffusion/dec-2021/clip_text_enc.pt --output models/clip_text_enc.pt

pip install git+https://github.com/openai/glide-text2im