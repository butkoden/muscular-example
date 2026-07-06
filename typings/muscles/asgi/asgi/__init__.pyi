from typing import Any, Callable

class AsgiStrategy: ...

class BaseResponse:
    def __init__(
        self,
        status: int = ...,
        body: Any = ...,
        headers: Any = ...,
        content_type: str | None = ...,
        **kwargs: Any,
    ) -> None: ...

class _Routes:
    def init(self, path: str, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

routes: _Routes

