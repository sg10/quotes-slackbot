import os
import random
import textwrap
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

from quotes_slackbot.config import config


def assemble_image_and_text(image: Image, text: str) -> Image:
    fonts = [
        f"{config.fonts_folder}/{f}"
        for f in os.listdir(config.fonts_folder)
        if f.endswith(".ttf")
    ]
    if config.fonts_whitelist:
        fonts = [f for f in fonts if f in config.fonts_whitelist]

    text_font = random.choice(fonts)
    font_size = 40
    text_color = (255, 255, 255)
    text_color_shadow = (90, 90, 90)
    char_per_line = 19

    image = image.resize((config.final_image_size, config.final_image_size))

    font = ImageFont.truetype(text_font, size=font_size)

    draw = ImageDraw.Draw(image)

    w, h = image.size
    lines = textwrap.wrap(text, width=char_per_line)
    lines.reverse()
    y_text = h - int(h * 0.1)
    for line in lines:
        width, _ = font.getsize(line)
        _, height = font.getsize("W")
        y_text -= height
        # shadow
        draw.text(
            ((w - width) / 2 + 1, y_text + 1), line, font=font, fill=text_color_shadow
        )
        # text
        draw.text(((w - width) / 2, y_text), line, font=font, fill=text_color)

    if config.logo_url:
        response = requests.get(config.logo_url)
        logo_img = Image.open(BytesIO(response.content))
        img_w, img_h = logo_img.size
        ratio = img_h / img_w
        new_logo_size = int(w / 4), int((w / 4) * ratio)
        logo_img = logo_img.resize(new_logo_size)

        img_w, img_h = logo_img.size
        offset = ((w - img_w - 15), 15)
        image.paste(logo_img, offset, logo_img)

    return image
