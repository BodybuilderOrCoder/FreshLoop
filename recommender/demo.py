"""Demo script: shows cache MISS then HIT, and writes example outputs."""
import json
import logging
from . import cache, preprocess
from .service import get_recommendations_with_meta


def main():
    logging.basicConfig(level=logging.WARNING)
    inter = preprocess.load_interactions()
    users = inter["user_id"].drop_duplicates().head(2).tolist() + ["new-user-without-history"]
    out = {}
    for uid in users:
        cache.invalidate(uid)  # make sure the first call is a MISS
        for attempt in (1, 2):
            items, status, ms = get_recommendations_with_meta(uid, inter)
            print(f"[{status}] user={uid[:8]}.. call #{attempt}: {ms:.2f} ms, "
                  f"{len(items)} items, first item source: {items[0]['source']}")
        out[uid] = items
    with open("recommender/sample_output/example_recommendations.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("Wrote recommender/sample_output/example_recommendations.json")


if __name__ == "__main__":
    main()