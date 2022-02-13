import json
import os
from typing import List, Optional

from pydantic import BaseSettings, Field

JSON_CONFIG_FILENAME = "config.json"


class BotConfig(BaseSettings):
    port: int = 8000
    host: str = "0.0.0.0"

    # if a task is triggered but not picked up for N seconds,
    #  it is dismissed
    tasks_timeout: int = 2 * 60 * 60

    send_post_preview: bool = False
    post_preview: str
    post_text_working: str
    post_text_done: str
    thread_post_preview: str = "(Quote details)"

    slack_token: str = Field(..., env="SLACK_API_TOKEN")
    channel_id: str

    gpt3_prompt: str
    gpt3_retries: int = 5
    gpt3_delimiter: str = "---"
    gpt3_tokens: int = 35
    gpt3_temperature: float = 1.0
    gpt3_frequency_penalty: int = 3
    gpt3_stop: str = "\n"
    gpt3_engine: str = "davinci"
    gpt3_openai_api_key: str = Field(..., env="OPENAI_KEY")

    glide_timestep_respacing: int = 100
    glide_guidance_scale: float = 3.0
    upsampling_respacing: str = "fast27"
    final_image_size: int = 512

    logo_url: Optional[str]
    fonts_folder: str = "/usr/local/share/fonts"
    fonts_whitelist: Optional[List[str]] = None


config = None
if not config:
    if os.path.exists(JSON_CONFIG_FILENAME):
        with open(JSON_CONFIG_FILENAME, "r") as f:
            json_config = json.load(f)
    else:
        json_config = {}
    config = BotConfig(**json_config)
