from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sdk.adaptiveflags import AdaptiveFlagsClient


def main() -> None:
    client = AdaptiveFlagsClient(base_url="http://localhost:8000")

    print("1) Tracking user event...")
    tracked = client.track(
        user_id="checkout_user_50",
        feature_key="checkout_upsell",
        event_type="checkout_upsell_shown",
        properties={
            "device": "desktop",
            "source_app": "shop-web",
            "activity_name": "Viu oferta no checkout",
        },
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
        feature_key="checkout_upsell",
        user_id="checkout_user_50",
        context={"country": "BR", "plan": "pro"},
    )
    print(decision)


if __name__ == "__main__":
    main()
