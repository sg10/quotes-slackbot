import datetime
import logging
import subprocess
from asyncio import Lock, TimeoutError, sleep, wait_for
from subprocess import PIPE, STDOUT
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.background import BackgroundTasks

from quotes_slackbot.config import config

app = FastAPI()

logger = logging.getLogger(__name__)


class GenerateTask(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    channel_id: str
    created: datetime.datetime = Field(default_factory=datetime.datetime.now)


tasks = []


@app.get("/status")
async def info():
    return {"number of tasks in the queue": len(tasks)}


@app.get("/trigger")
async def info(channel_id, background_tasks: BackgroundTasks):
    task = GenerateTask(channel_id=channel_id)
    tasks.append(task)
    background_tasks.add_task(generate_image, task)
    return f"{task.task_id} queued"


busy_lock = None
generate_thread = None


async def generate_image(task: GenerateTask):
    global busy_lock
    busy_lock = busy_lock or Lock()

    logger.info(f"Queueing {task.task_id}")

    try:
        await wait_for(busy_lock.acquire(), timeout=config.tasks_timeout)
    except TimeoutError:
        logger.error(f"Timeout for {task.task_id}")
        return

    logger.info(f"Starting {task.task_id}")

    process = subprocess.Popen(
        ["python3", "-m", "quotes_slackbot.quote_generator"],
        stderr=STDOUT,
        stdout=PIPE,
        text=True,
    )
    while process.poll() is None:
        if line := process.stdout.readline():
            logger.info(f" --- {line.strip()}")
        await sleep(0.5)

    logger.info(f"Done {task.task_id}")

    busy_lock.release()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host=config.host, port=config.port, workers=1)
