import asyncio
import base64
from functools import cache
from typing import cast
from uuid import uuid4

from uvicorn import Server


def generate_unique_slug(length: int = 12) -> str:
    random_uuid = uuid4()
    base64_slug = (
        base64.urlsafe_b64encode(random_uuid.bytes).decode("utf-8").rstrip("=")
    )
    return base64_slug[:length]


@cache
def uvicorn_server() -> Server:
    """
    Hack because sse-starlette cannot handle signals properly
    when using uvicorn.
    TODO: find better way to find server instance
    """
    for task in asyncio.all_tasks():
        coro = task.get_coro()
        if not coro:
            continue
        frame = coro.cr_frame
        if not frame:
            continue
        args = frame.f_locals
        self = args.get("self")
        if self and isinstance(self, Server):
            return cast(Server, self)
    raise RuntimeError("Uvicorn server not found")


def uvicorn_should_exit() -> bool:
    server = uvicorn_server()
    return server.should_exit


def debugger() -> None:
    try:
        from remote_pdb import RemotePdb  # type: ignore
    except ImportError:
        logger.warn("No remote_pdb, skipping debugger")
        return

    RemotePdb("127.0.0.1", 4444).set_trace()
