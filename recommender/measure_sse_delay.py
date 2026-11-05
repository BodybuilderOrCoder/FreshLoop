"""Measure SSE propagation delay from FreshLoop inventory stream."""
import json
import sys
import time
import urllib.request

API_BASE = "http://localhost:8000"


def measure_sse(warehouse_id: str, max_events: int = 3):
    """Subscribe to warehouse inventory events and record incoming events."""
    url = f"{API_BASE}/api/warehouses/{warehouse_id}/inventory/events?poll_interval_seconds=1.0"
    print(f"Subscribing to SSE stream: {url}")
    print("Tip: Trigger stock updates in Swagger UI or via database to see real-time changes.")

    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    received_count = 0

    try:
        with urllib.request.urlopen(req) as response:
            event_name = None
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data_str = line.split(":", 1)[1].strip()
                    now = time.strftime("%H:%M:%S")
                    print(f"[{now}] Event received: '{event_name}'")
                    try:
                        payload = json.loads(data_str)
                        if event_name == "inventory_snapshot":
                            print(f"  -> Snapshot received: {len(payload)} items.")
                        elif event_name == "inventory_change":
                            print(
                                f"  -> Change detected! Added: {len(payload.get('added', []))}, "
                                f"Updated: {len(payload.get('updated', []))}, "
                                f"Removed: {len(payload.get('removed', []))}"
                            )
                    except Exception:
                        print(f"  -> Raw payload: {data_str[:60]}...")

                    received_count += 1
                    if received_count >= max_events:
                        print("Test completed successfully.")
                        break
    except Exception as exc:
        print(f"SSE connection failed: {exc}")
        print("Note: Verify that the FastAPI backend is running on port 8000.")


if __name__ == "__main__":
    wh_id = sys.argv[1] if len(sys.argv) > 1 else "00000000-0000-0000-0000-000000000001"
    measure_sse(wh_id)