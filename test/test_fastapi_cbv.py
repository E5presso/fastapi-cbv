from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from fastapi_cbv.app import App
from fastapi_cbv.controller import AbstractBaseController
from fastapi_cbv.routing import get
from fastapi_cbv.global_dependency import (
    Component,
    Controller,
    Autowired,
    inject,
)
from dependency_injector.providers import Factory
from dependency_injector.containers import DeclarativeContainer
from httpx import AsyncClient
import asyncio
import pytest


@pytest.mark.asyncio
async def test_create_app() -> None:
    class ITest(ABC):
        @abstractmethod
        def say_hello(self) -> str:
            ...

    @Component(provider=Factory, name="Sarah")
    class Test(ITest):
        __id: UUID
        __name: str

        def __init__(self, name: str) -> None:
            self.__id = uuid4()
            self.__name = name

        def say_hello(self) -> str:
            return f"Hello {self.__name}:{self.__id}"

    class AnotherTest(ITest):
        def say_hello(self) -> str:
            return "I'm not OK!"

    class TestContainer(DeclarativeContainer):
        test: Factory[ITest] = Factory(AnotherTest)

    @Controller("/test")
    class TestController(AbstractBaseController):
        __test: ITest
        __another_test: ITest

        @Autowired()
        def __init__(
            self,
            test: ITest = inject(Test, fastapi=True),
            another_test: ITest = inject(TestContainer.test, fastapi=True),
        ) -> None:
            super().__init__()
            self.__test = test
            self.__another_test = another_test

        @get("")
        async def run(self) -> str:
            return self.__test.say_hello()

        @get("/another")
        async def run_another(self) -> str:
            return self.__another_test.say_hello()

    is_background_task_done: bool = False

    async def background_task() -> None:
        nonlocal is_background_task_done
        await asyncio.sleep(0.1)
        is_background_task_done = True

    app: App = App().configure(
        lambda app: app.inject_dependency_container(
            TestContainer(), [TestController]
        ).inject_background_task(background_task)
    )

    assert is_background_task_done == False
    await asyncio.sleep(0.3)
    assert is_background_task_done == True

    client: AsyncClient = AsyncClient(app=app, base_url="http://test")

    result1: str = (await client.get("/test")).json()
    result2: str = (await client.get("/test")).json()
    result3: str = (await client.get("/test/another")).json()
    assert result1.startswith("Hello Sarah")
    assert result1 != result2
    assert result3 == "I'm not OK!"


@pytest.mark.asyncio
async def test_app_with_background_task_loop() -> None:
    async def background_task() -> None:
        while True:
            print("Loop is still running!")
            await asyncio.sleep(0.1)

    app: App = App().configure(
        lambda app: app.inject_background_task(background_task)
    )
    _: AsyncClient = AsyncClient(app=app, base_url="http://test")
    await asyncio.sleep(0.3)
