from abc import ABC
from enum import Enum
from typing import Any, Callable, TypeVar
from functools import partial
from fastapi import Depends
from fastapi.routing import APIRouter
from .error import ControllerNotPropertyDecoratedError
from ._args import EndpointDefinition, WebSocketDefinition
import dataclasses

AnyCallable = TypeVar("AnyCallable", bound=Callable[..., Any])


class AbstractBaseController(ABC):
    _prefix: str
    _tags: list[str | Enum] | None
    _endpoints: list[EndpointDefinition] = []
    _websockets: list[WebSocketDefinition] = []
    router: APIRouter

    def __init__(self) -> None:
        if (
            not hasattr(self, "_prefix")
            or not hasattr(self, "_endpoints")
            or not hasattr(self, "_websockets")
        ):
            raise ControllerNotPropertyDecoratedError
        self.router = APIRouter(prefix=self._prefix, tags=self._tags)
        for endpoint in self._endpoints:
            self.router.add_api_route(
                endpoint=partial(endpoint.method, self=Depends(type(self))),
                **dataclasses.asdict(endpoint.args),
            )
        for websocket in self._websockets:
            self.router.add_api_websocket_route(
                endpoint=partial(websocket.method, self=Depends(type(self))),
                **dataclasses.asdict(websocket.args),
            )
