class DependencyAlreadyExistsError(BaseException):
    ...


class ControllerNotPropertyDecoratedError(BaseException):
    def __str__(self) -> str:
        return "This Controller is not properly decorated. please decorate your controller you want to use with @Controller decorator."
