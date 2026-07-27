from typing import Any, Iterable


class ActionAsgiAdapter:
    @classmethod
    def from_application(
        cls,
        app: Any,
        *,
        allowed_actions: Iterable[str] | None = ...,
        path_prefix: str = ...,
        get_actions: Iterable[str] | None = ...,
    ) -> Any: ...
