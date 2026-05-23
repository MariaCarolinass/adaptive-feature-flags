from __future__ import annotations

from sdk.smartflags import SmartFlagsClient


def main() -> None:
    client = SmartFlagsClient(base_url="http://localhost:8000")

    print("1) Tracking user event...")
    tracked = client.track(
        user_id="external_user_123",
        feature_key="new_checkout",
        event_type="viewed_feature",
        properties={"device": "mobile", "source_app": "shop-web"},
    )
    print(tracked)

    print("\n2) Triggering training...")
    trained = client.train()
    print(trained)

    print("\n3) Checking model status...")
    status = client.model_status()
    print(status)

    print("\n4) Evaluating feature for a user...")
    decision = client.evaluate(
        feature_key="new_checkout",
        user_id="external_user_123",
        context={"country": "BR", "plan": "pro"},
    )
    print(decision)


if __name__ == "__main__":
    main()
