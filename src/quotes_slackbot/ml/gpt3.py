import logging

import openai

from quotes_slackbot.config import config

logger = logging.getLogger(__name__)


def query_gpt3(prompt: str):
    if not openai.api_key:
        openai.api_key = config.gpt3_openai_api_key

    if prompt[-1] != config.gpt3_stop:
        prompt += config.gpt3_stop

    response = openai.Completion.create(
        engine=config.gpt3_engine,
        prompt=prompt,
        temperature=config.gpt3_temperature,
        max_tokens=config.gpt3_tokens,
        top_p=1,
        frequency_penalty=config.gpt3_frequency_penalty,
        presence_penalty=0,
        stop=[config.gpt3_stop],
    )

    return response["choices"][0]["text"]
