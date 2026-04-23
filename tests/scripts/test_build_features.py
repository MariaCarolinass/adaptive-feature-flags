from __future__ import annotations

import pandas as pd

from scripts.build_features import build_features_from_chunks


def test_build_features_from_chunks_aggregates_across_chunks() -> None:
    chunk1 = pd.DataFrame(
        [
            {"user_id": "u1", "event_type": "view", "timestamp": "2026-01-01T10:00:00Z", "feature_key": "f1"},
            {"user_id": "u1", "event_type": "addtocart", "timestamp": "2026-01-01T11:00:00Z", "feature_key": "f1"},
            {"user_id": "u2", "event_type": "view", "timestamp": "2026-01-01T12:00:00Z", "feature_key": "f2"},
        ]
    )
    chunk2 = pd.DataFrame(
        [
            {"user_id": "u1", "event_type": "transaction", "timestamp": "2026-01-02T10:00:00Z", "feature_key": "f3"},
            {"user_id": "u2", "event_type": "view", "timestamp": "2026-01-02T08:00:00Z", "feature_key": "f2"},
        ]
    )

    features = build_features_from_chunks(iter([chunk1, chunk2]))

    u1 = features.loc[features["user_id"] == "u1"].iloc[0]
    u2 = features.loc[features["user_id"] == "u2"].iloc[0]

    assert int(u1["total_events"]) == 3
    assert int(u1["positive_events"]) == 2
    assert int(u1["view_events"]) == 1
    assert int(u1["cart_events"]) == 1
    assert int(u1["purchase_events"]) == 1
    assert int(u1["unique_features"]) == 2
    assert int(u1["active_days"]) == 2
    assert int(u1["target"]) == 1

    assert int(u2["total_events"]) == 2
    assert int(u2["positive_events"]) == 0
    assert int(u2["target"]) == 0
