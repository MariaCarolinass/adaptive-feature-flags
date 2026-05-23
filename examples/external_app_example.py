from __future__ import annotations

from sdk.adaptiveflags import AdaptiveFlagsClient


def render_checkout(user_id: str, *, enabled: bool) -> None:
    if enabled:
        print(f"[{user_id}] Rendering NEW checkout experience.")
        return
    print(f"[{user_id}] Rendering DEFAULT checkout experience.")


def handle_user_request(user_id: str) -> None:
    client = AdaptiveFlagsClient(base_url="http://localhost:8000")

    decision = client.evaluate("new_checkout", user_id)
    enabled = bool(decision.get("enabled", False))

    render_checkout(user_id, enabled=enabled)

    event_type = "viewed_feature" if enabled else "viewed_default_checkout"
    tracked = client.track(
        user_id=user_id,
        feature_key="new_checkout",
        event_type=event_type,
        properties={"surface": "checkout_page"},
    )
    print(f"[{user_id}] Event tracked with id={tracked.get('id')}")


def main() -> None:
    for user_id in ["u1001", "u1002"]:
        handle_user_request(user_id)


if __name__ == "__main__":
    main()
