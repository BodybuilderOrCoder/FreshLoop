"""Benchmark Redis Cache HIT vs MISS latency for FreshLoop Recommender."""
import csv
import logging
from pathlib import Path
import numpy as np
import pandas as pd

from recommender import cache, config
from recommender.service import get_recommendations_with_meta

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("benchmark")

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIONS_PATH = REPO_ROOT / "database" / "data" / "train_interactions.csv"
OUTPUT_CSV = REPO_ROOT / "recommender" / "sample_output" / "cache_latency_benchmark.csv"


def run_benchmark(num_users: int = 30, hit_iterations: int = 10):
    if not INTERACTIONS_PATH.exists():
        fallback_path = REPO_ROOT / "recommender" / "sample_output" / "interactions_sample.csv"
        df = pd.read_csv(fallback_path)
    else:
        df = pd.read_csv(INTERACTIONS_PATH)

    available_users = df["user_id"].dropna().unique().tolist()
    test_users = available_users[:num_users]

    log.info("Starting benchmark with %d users...", len(test_users))

    miss_latencies = []
    hit_latencies = []

    # 1. Đo Cache MISS (Xóa cache trước khi gọi)
    log.info("--- Testing Cache MISS ---")
    for user_id in test_users:
        try:
            cache.invalidate(user_id, algorithm="baseline", top_k=10)
        except Exception:
            pass
        _, status, elapsed_ms = get_recommendations_with_meta(
            user_id=user_id,
            inter=df,
            top_k=10,
            algorithm="baseline",
        )
        if status == "MISS":
            miss_latencies.append(elapsed_ms)

    # 2. Đo Cache HIT (Gọi lại nhiều lần khi đã có cache)
    log.info("--- Testing Cache HIT ---")
    for _ in range(hit_iterations):
        for user_id in test_users:
            _, status, elapsed_ms = get_recommendations_with_meta(
                user_id=user_id,
                inter=df,
                top_k=10,
                algorithm="baseline",
            )
            if status == "HIT":
                hit_latencies.append(elapsed_ms)

    # Tính toán p50, p95
    p50_miss = np.percentile(miss_latencies, 50) if miss_latencies else 0.0
    p95_miss = np.percentile(miss_latencies, 95) if miss_latencies else 0.0

    p50_hit = np.percentile(hit_latencies, 50) if hit_latencies else 0.0
    p95_hit = np.percentile(hit_latencies, 95) if hit_latencies else 0.0

    print("\n========== KẾT QUẢ BENCHMARK (ms) ==========")
    print(f"Cache MISS (N={len(miss_latencies)}): p50 = {p50_miss:.2f} ms | p95 = {p95_miss:.2f} ms")
    print(f"Cache HIT  (N={len(hit_latencies)}):  p50 = {p50_hit:.2f} ms | p95 = {p95_hit:.2f} ms")
    print("============================================\n")

    # Lưu vào file CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "sample_count", "p50_ms", "p95_ms", "mean_ms"])
        if miss_latencies:
            writer.writerow(["cache_miss", len(miss_latencies), round(p50_miss, 2), round(p95_miss, 2), round(float(np.mean(miss_latencies)), 2)])
        if hit_latencies:
            writer.writerow(["cache_hit", len(hit_latencies), round(p50_hit, 2), round(p95_hit, 2), round(float(np.mean(hit_latencies)), 2)])

    log.info("Results saved to: %s", OUTPUT_CSV)


if __name__ == "__main__":
    run_benchmark()