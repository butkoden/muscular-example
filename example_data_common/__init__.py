from __future__ import annotations

DEVELOPMENT_APPROACH = {
    "contract": "Each adapter example registers one external data adapter package explicitly.",
    "use_case": "Data operations live in the example use-case module, away from web adapters.",
    "adapter": "Application code depends on muscles-data typed ports, not vendor SDK clients.",
}


def development_approach() -> dict:
    return dict(DEVELOPMENT_APPROACH)
