from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from muscles import ApiKeyAuthSecurity, JsonResponse, cors


DEFAULT_API_KEY_HEADER = "X-Api-Key"
DEFAULT_API_KEY_TOKEN = "demo-framework-token"
DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_PROTECTED_PREFIX = "/protected"


@dataclass(frozen=True)
class ApiKeyPolicy:
    token: str
    header_name: str = DEFAULT_API_KEY_HEADER
    status_code: int = 401
    error_message: str = "unauthorized"
    error_code: str = "unauthorized"

    def build_unauthorized_response(self):
        return JsonResponse({"error_code": self.error_code, "error": self.error_message}, status=self.status_code)

    @property
    def openapi_security(self):
        return [ApiKeyAuthSecurity(name=self.header_name, key="ApiKey")]

    @staticmethod
    def _header_value(request, name: str):
        expected = name.lower()
        for key, value in (request.headers or {}).items():
            if str(key).lower() == expected:
                return value
        return None

    def guard(self, request):
        if self._header_value(request, self.header_name) != self.token:
            return self.build_unauthorized_response()
        return None


class RouteRegistrar:
    def __init__(
        self,
        *,
        routes: Any,
        api: Any,
        response_class: Any,
        api_prefix: str = DEFAULT_API_PREFIX,
        api_key_token: str,
        api_key_header: str = DEFAULT_API_KEY_HEADER,
        protected_prefix: str = DEFAULT_PROTECTED_PREFIX,
    ):
        self.routes = routes
        self.api = api
        self.response_class = response_class
        self.api_prefix = api_prefix.rstrip("/")
        self.protected_prefix = protected_prefix
        self.api_key_policy = ApiKeyPolicy(token=api_key_token, header_name=api_key_header)

    @property
    def protected_guard_pattern(self):
        if self.protected_prefix.startswith("/"):
            return f"{self.api_prefix}/{self.protected_prefix.strip('/')}/**"
        return f"{self.api_prefix}/{self.protected_prefix.rstrip('/')}/**"

    @property
    def openapi_security(self):
        return self.api_key_policy.openapi_security

    def attach_api_contract(self, *, allow_origins, allow_methods, allow_headers):
        self.api.use(cors(
            allow_origins=allow_origins,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
        ))
        self.api.guard(self.protected_guard_pattern, self.api_key_policy.guard)
        return self

    def page(self, path, key: str, method: str = "GET", **kwargs):
        return self.routes.init(path, key=key, method=method, **kwargs)

    def api_controller(self, route: str, *args, **kwargs):
        return self.api.controller(route, *args, **kwargs)

    def api_group(self, path: str, **kwargs):
        return self.api.group(path, **kwargs)

    def api_action(self, group: Any, path: str, method: str, **kwargs):
        return group.init(path, method=method, **kwargs)
