from abc import ABC, abstractmethod
from typing import Awaitable, Callable, TypeAlias
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

NextMiddleware: TypeAlias = Callable[[Request], Awaitable[Response]]


class IMiddleware(ABC, BaseHTTPMiddleware):
    @abstractmethod
    async def dispatch(
        self, request: Request, call_next: NextMiddleware
    ) -> Response:
        return await call_next(request)
