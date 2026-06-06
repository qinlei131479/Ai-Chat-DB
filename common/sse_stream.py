"""
SSE 流式响应适配层，供 Agent / llm_service 通过 write() 推送数据。
与具体 Web 框架（FastAPI）解耦。
"""

import asyncio
from typing import Any, Awaitable, Callable

from starlette.requests import Request
from starlette.responses import StreamingResponse


class SSEStreamBase:
    """协议无关的 SSE 写入器"""

    def __init__(self, request: Request):
        self.request = request

    async def write(self, data: str) -> None:
        raise NotImplementedError


class FastAPISSEStream(SSEStreamBase):
    """基于 asyncio.Queue 的 FastAPI SSE 写入器"""

    def __init__(self, request: Request, queue: asyncio.Queue):
        super().__init__(request)
        self._queue = queue

    async def write(self, data: str) -> None:
        await self._queue.put(data)


_SENTINEL = object()


async def _sse_generator(queue: asyncio.Queue, stream_task: asyncio.Task):
    """从队列读取 chunk 并 yield，直到流任务结束且队列排空"""
    try:
        while True:
            if stream_task.done() and queue.empty():
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if stream_task.done():
                    if queue.empty():
                        break
                    continue
                continue
            if item is _SENTINEL:
                break
            yield item
    finally:
        if not stream_task.done():
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass


async def _run_stream(stream: FastAPISSEStream, handler: Callable[..., Awaitable[Any]]):
    try:
        await handler(stream)
    finally:
        await stream._queue.put(_SENTINEL)


def create_sse_response(
    request: Request,
    handler: Callable[[SSEStreamBase], Awaitable[Any]],
) -> StreamingResponse:
    """
    创建 SSE StreamingResponse。

    handler 接收 SSEStreamBase 实例，通过 await stream.write(...) 推送数据。
    """
    queue: asyncio.Queue = asyncio.Queue()
    stream = FastAPISSEStream(request, queue)
    task = asyncio.create_task(_run_stream(stream, handler))
    return StreamingResponse(
        _sse_generator(queue, task),
        media_type="text/event-stream",
    )
