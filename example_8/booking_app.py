from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from muscles import ApplicationMeta, Column, Context, Integer, Model, String, action
from muscles.asgi import AsgiStrategy
from muscles.asgi.action_bridge import ActionAsgiAdapter
from muscles_mcp import McpStrategy, build_model_json_schema


class BookingCreate(Model):
    """The single input contract shared by every projection."""

    title = Column(String, nullable=False, min_length=1)
    guest_count = Column(Integer, default=1)


@dataclass
class BookingUseCase:
    """Small business use case with no knowledge of transport details."""

    def create(self, *, title: str, guest_count: int) -> dict[str, Any]:
        return {
            "id": 1,
            "title": title,
            "guest_count": guest_count,
            "status": "created",
        }


class BookingApp(metaclass=ApplicationMeta):
    """One application model shared by HTTP, CLI, and MCP projections."""

    asgi_public = Context(cast(Any, AsgiStrategy), params={"profile": "public"})
    mcp_public = Context(cast(Any, McpStrategy), transport=asgi_public, params={"mcp_profile": "public"})


app = BookingApp()
booking_use_case = BookingUseCase()


def _mcp_metadata() -> dict[str, Any]:
    return {
        "mcp": {
            "route": "/create",
            "full_route": "/bookings/create",
            "name": "bookings.create",
            "transport": "mcp",
            "server": "public",
            "servers": ["public"],
        }
    }


@action(
    app,
    name="bookings.create",
    description="Create a booking request",
    input_schema=build_model_json_schema(BookingCreate),
    output_schema={
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "guest_count": {"type": "integer"},
            "status": {"type": "string"},
        },
        "required": ["id", "title", "guest_count", "status"],
    },
    transports=["http", "cli", "mcp"],
    metadata=_mcp_metadata(),
)
def create_booking(payload: dict[str, Any], _context) -> dict[str, Any]:
    """Keep business behavior in one use case; adapters only select transport."""

    return booking_use_case.create(
        title=str(payload["title"]),
        guest_count=int(payload.get("guest_count", 1)),
    )


http_application = ActionAsgiAdapter.from_application(
    app,
    allowed_actions={"bookings.create"},
    path_prefix="/actions",
)
asgi_application = http_application
