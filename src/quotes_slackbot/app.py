import datetime
import logging
import subprocess
from asyncio import Lock, TimeoutError, sleep, wait_for
from subprocess import PIPE, STDOUT
from typing import Optional
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.background import BackgroundTasks
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from quotes_slackbot.config import config
from quotes_slackbot.quote_generator import fetch_quote_and_motive

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

logger = logging.getLogger(__name__)


class GenerateTask(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    channel_id: str
    created: datetime.datetime = Field(default_factory=datetime.datetime.now)
    quote: Optional[str] = None
    motive: Optional[str] = None


tasks = []


@app.get("/status")
async def info():
    return {"queued": len(tasks)}


@app.get("/fetch-next")
async def fetch_next(num: int = 1):
    return [fetch_quote_and_motive() for _ in range(num)]


@app.get("/trigger")
async def trigger(
    background_tasks: BackgroundTasks,
    channel_id: Optional[str],
    quote: Optional[str] = None,
    motive: Optional[str] = None,
):
    task = GenerateTask(channel_id=channel_id, quote=quote, motive=motive)
    tasks.append(task)
    background_tasks.add_task(generate_image, task)
    return f"{task.task_id} queued"


@app.get("/console")
async def console():
    return FileResponse("static/index.html")


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

    quote_and_motive = [task.quote, task.motive] if task.quote and task.motive else []
    process_args = [
        "python3",
        "-m",
        "quotes_slackbot.quote_generator",
    ] + quote_and_motive
    logger.info(process_args)

    process = subprocess.Popen(
        process_args,
        stderr=STDOUT,
        stdout=PIPE,
        text=True,
    )
    while process.poll() is None:
        if line := process.stdout.readline():
            logger.info(f" --- {line.strip()}")
        await sleep(0.5)

    logger.info(f"Done {task.task_id}")
    tasks.remove(task)

    busy_lock.release()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host=config.host, port=config.port, workers=1)
