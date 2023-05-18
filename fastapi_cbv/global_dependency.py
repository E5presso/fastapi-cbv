from enum import Enum
from inspect import FullArgSpec, getfullargspec
from types import FunctionType, MethodType
from typing import Any, Callable, Type, TypeVar
from dependency_injector.containers import DynamicContainer
from dependency_injector.providers import Provider
from dependency_injector.wiring import Provide
from dependency_injector import wiring
from fastapi import Depends
from fastapi.exceptions import FastAPIError
from fastapi.utils import create_response_field
from .controller import AbstractBaseController
from ._args import (
    EndpointDefinition,
    RouteArgs,
    SocketArgs,
    WebSocketDefinition
)
from .utils.casing import pascal_to_snake
import inspect

TInterface = TypeVar("TInterface", bound=Type)
TDependency = TypeVar("TDependency", bound=Type)
TFunc = TypeVar("TFunc", bound=Callable[..., Any])
RegisteredModules: list[str] = []
RegisteredControllers: list[Type[AbstractBaseController]] = []
ApplicationContext: DynamicContainer = DynamicContainer()


class Component:
    __provider: Provider | Any
    __key: str | None
    __constructor_kwargs: dict[str, Any]

    def __init__(
        self,
        provider: Provider | Any,
        key: str | None = None,
        **constructor_kwargs
    ) -> None:
        self.__provider = provider
        self.__key = key
        self.__constructor_kwargs = constructor_kwargs

    def __call__(self, dependency: TDependency) -> TDependency:
        argspec: FullArgSpec = getfullargspec(dependency.__init__)
        conditions: list[bool] = [
            argspec.annotations.get(k) != type(v)
            for k, v in self.__constructor_kwargs.items()
        ]
        if len(argspec.args[1:]) != len(self.__constructor_kwargs):
            raise TypeError
        if any(conditions):
            raise TypeError
        if self.__key is not None:
            ApplicationContext.set_provider(
                self.__key,
                self.__provider(dependency, **self.__constructor_kwargs),
            )
        else:
            ApplicationContext.set_provider(
                pascal_to_snake(dependency.__name__),
                self.__provider(dependency, **self.__constructor_kwargs),
            )
        return dependency


class Autowired:
    def __init__(self) -> None:
        return

    def __call__(self, func: TFunc) -> TFunc:
        global RegisteredModules
        RegisteredModules += [func.__module__]
        RegisteredModules = list(set(RegisteredModules))
        return wiring.inject(func)


class Controller:
    __prefix: str
    __tags: list[str | Enum] | None

    def __init__(
        self, prefix: str, tags: list[str | Enum] | None = None
    ) -> None:
        self.__prefix = prefix
        self.__tags = tags

    def __call__(
        self, controller: Type[AbstractBaseController]
    ) -> Type[AbstractBaseController]:
        def function_predicate(obj: Any) -> bool:
            return isinstance(obj, FunctionType)

        endpoints: list[EndpointDefinition] = []
        websockets: list[WebSocketDefinition] = []
        methods: list[tuple[str, MethodType]] = inspect.getmembers(
            controller, predicate=function_predicate
        )
        for _, method in methods:
            if hasattr(method, "_endpoint"):
                endpoint: EndpointDefinition = getattr(method, "_endpoint")
                endpoint_method: Callable[..., Any] = endpoint.method
                endpoint_args: RouteArgs = endpoint.args
                return_type: Type[Any] | None = inspect.signature(
                    endpoint_method
                ).return_annotation
                if endpoint.args.name is None:
                    endpoint.args.name = " ".join(
                        list(
                            map(
                                lambda x: x.capitalize(),
                                endpoint.method.__name__.split("_"),
                            )
                        )
                    )
                if endpoint.args.description is None:
                    endpoint.args.description = endpoint.method.__doc__
                if return_type is not None:
                    try:
                        create_response_field("", return_type)
                    except FastAPIError:
                        ...
                    else:
                        endpoint_args.response_model = return_type
                endpoints.append(
                    EndpointDefinition(
                        method=endpoint_method, args=endpoint_args
                    )
                )
            elif hasattr(method, "_websocket"):
                websocket: WebSocketDefinition = getattr(method, "_websocket")
                websocket_method: Callable[..., Any] = websocket.method
                websocket_args: SocketArgs = websocket.args
                if websocket.args.name is None:
                    websocket.args.name = " ".join(
                        list(
                            map(
                                lambda x: x.capitalize(),
                                websocket.method.__name__.split("_"),
                            )
                        )
                    )
                websockets.append(
                    WebSocketDefinition(
                        method=websocket_method, args=websocket_args
                    )
                )

        controller._prefix = self.__prefix
        controller._tags = self.__tags
        controller._endpoints = endpoints
        controller._websockets = websockets

        global RegisteredControllers
        RegisteredControllers += [controller]
        return controller


def inject(
    key: str | Type[TDependency] | Provider[TDependency],
    fastapi: bool = False,
) -> TDependency:
    if isinstance(key, str):
        if fastapi:
            return Depends(Provide[getattr(ApplicationContext, key)])
        return Provide[getattr(ApplicationContext, key)]
    if isinstance(key, Provider):
        if fastapi:
            return Depends(Provide[key])
        return Provide[key]
    if fastapi:
        return Depends(
            Provide[getattr(ApplicationContext, pascal_to_snake(key.__name__))]
        )
    return Provide[getattr(ApplicationContext, pascal_to_snake(key.__name__))]
