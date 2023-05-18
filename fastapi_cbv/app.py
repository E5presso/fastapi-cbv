from __future__ import annotations
from asyncio import create_task, Task
from typing import Any, Callable, Coroutine, Type
from fastapi import FastAPI
from dependency_injector.containers import Container
from .controller import AbstractBaseController
from .global_dependency import (
    ApplicationContext,
    RegisteredControllers,
    RegisteredModules,
)
from .error import DependencyAlreadyExistsError


class App(FastAPI):
    __tasks: list[Task[None]]
    __dependencies: dict[Type, Container]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__tasks = []
        self.__dependencies = {}
        ApplicationContext.wire(modules=RegisteredModules)
        for controller in RegisteredControllers:
            controller_instance: AbstractBaseController = controller()
            try:
                super().include_router(router=controller_instance.router)
            except Exception as e:
                raise e from e

    def configure(self, configure: Callable[[App], App]) -> App:
        return configure(self)

    def inject_middleware(self, middleware_class: Type, **options) -> App:
        super().add_middleware(middleware_class, **options)
        return self

    def inject_dependency_container(
        self, dependency: Container, modules: list[Any]
    ) -> App:
        if self.__dependencies.get(type(dependency)) is not None:
            raise DependencyAlreadyExistsError
        dependency.wire(modules=[x.__module__ for x in modules])
        self.__dependencies[type(dependency)] = dependency
        return self

    def inject_background_task(
        self, background_task: Callable[..., Coroutine[Any, Any, None]]
    ) -> App:
        def on_task_done(task: Task) -> None:
            self.__tasks.remove(task)

        task: Task[None] = create_task(background_task())
        task.add_done_callback(on_task_done)
        self.__tasks.append(task)
        return self
