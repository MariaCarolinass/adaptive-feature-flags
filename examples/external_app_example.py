from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sdk.adaptiveflags import AdaptiveFlagsClient


def render_checkout(user_id: str, *, enabled: bool) -> None:
    if enabled:
        print(f"[{user_id}] Rendering NEW checkout experience.")
        return
    print(f"[{user_id}] Rendering DEFAULT checkout experience.")


def handle_user_request(user_id: str) -> None:
    client = AdaptiveFlagsClient(base_url="http://localhost:8000")

    decision = client.evaluate("checkout_upsell", user_id)
    enabled = bool(decision.get("enabled", False))

    render_checkout(user_id, enabled=enabled)

    event_type = "checkout_upsell_shown" if enabled else "view"
    tracked = client.track(
        user_id=user_id,
        feature_key="checkout_upsell",
        event_type=event_type,
        properties={
            "surface": "cart drawer",
            "activity_name": "Viu oferta no checkout" if event_type == "checkout_upsell_shown" else "Visualização",
        },
    )
    print(f"[{user_id}] Event tracked with id={tracked.get('id')}")


def main() -> None:
    for user_id in ["checkout_user_50", "checkout_user_49", "checkout_user_48"]:
        handle_user_request(user_id)


if __name__ == "__main__":
    main()
