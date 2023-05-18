from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, Type
from fastapi import Response, params
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.routing import Route

SetIntStr = set[int | str]
DictIntStrAny = dict[int | str, Any]


@dataclass
class RouteArgs:
    path: str
    response_model: Type[Any] | None = None
    status_code: int | None = None
    tags: list[str] | None = None
    dependencies: Sequence[params.Depends] | None = None
    summary: str | None = None
    description: str | None = None
    response_description: str = "Successful Response"
    responses: dict[int | str, dict[str, Any]] | None = None
    deprecated: bool | None = None
    methods: set[str] | list[str] | None = None
    operation_id: str | None = None
    response_model_include: SetIntStr | DictIntStrAny | None = None
    response_model_exclude: SetIntStr | DictIntStrAny | None = None
    response_model_by_alias: bool = True
    response_model_exclude_unset: bool = False
    response_model_exclude_defaults: bool = False
    response_model_exclude_none: bool = False
    include_in_schema: bool = True
    response_class: Type[Response] | DefaultPlaceholder = field(
        default_factory=lambda: Default(JSONResponse)
    )
    name: str | None = None
    route_class_override: Type[APIRoute] | None = None
    callbacks: list[Route] | None = None
    openapi_extra: dict[str, Any] | None = None

    class Config:
        arbitrary_types_allowed: bool = True


@dataclass
class SocketArgs:
    path: str
    name: str | None

    class Config:
        arbitrary_types_allowed: bool = True


@dataclass
class EndpointDefinition:
    method: Callable[..., Any]
    args: RouteArgs


@dataclass
class WebSocketDefinition:
    method: Callable[..., Any]
    args: SocketArgs
