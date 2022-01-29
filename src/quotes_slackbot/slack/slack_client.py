import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# SLACK_CHANNEL_ID = "C011Z8J8Y03"  # general


logger = logging.getLogger(__name__)


class SingleMessageSlackClient:
    def __init__(self, *, channel_id: str, token: str):
        self.channel_id = channel_id
        self.token = token
        self.client = WebClient(token)
        self.message_ts = None

    def put(self, *, blocks, text=None, file_content=None, filename="image.png"):
        try:
            if self.message_ts:
                assert not file_content
                self.client.chat_update(
                    channel=self.channel_id, ts=self.message_ts, blocks=blocks
                )
            elif file_content:
                assert text
                result = self.client.files_upload(
                    content=file_content,
                    filename=filename,
                    channels=self.channel_id,
                    text=text,
                )
                self.message_ts = result["file"]["shares"]["public"][self.channel_id][
                    0
                ]["ts"]
                self.client.chat_update(
                    text=text,
                    channel=self.channel_id,
                    ts=self.message_ts,
                    blocks=blocks,
                )
            else:
                assert text
                result = self.client.chat_postMessage(
                    channel=self.channel_id,
                    ts=self.message_ts,
                    blocks=blocks,
                    text=text,
                )
                self.message_ts = result["ts"]
            return True
        except SlackApiError as e:
            logger.error(e)
            return False

    def delete(self):
        if not self.message_ts:
            logger.error("No previous message")
            return False
        try:
            self.client.chat_delete(channel=self.channel_id, ts=self.message_ts)
            self.message_ts = None
            return True
        except SlackApiError as e:
            logger.error(e)
            return False

    def append_to_thread(self, blocks, text):
        assert self.message_ts
        self.client.chat_postMessage(
            channel=self.channel_id, text=text, blocks=blocks, thread_ts=self.message_ts
        )


def slack_markdown_block(text: str):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text,
        },
    }
