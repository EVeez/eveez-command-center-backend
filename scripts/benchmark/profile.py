import subprocess
import time
import os

"""
Lightweight profiler helper.
Usage: python scripts/benchmark/profile.py
It will hit a hot endpoint repeatedly while running scalene if available,
otherwise prints guidance for py-spy.
"""

HOT_URL = os.getenv("HOT_URL", "http://127.0.0.1:8000/api/v1/analytics/service-requests/summary?range=today")

def run_curl_bomb(seconds: int = 5):
    end = time.time() + seconds
    count = 0
    while time.time() < end:
        subprocess.run(["curl", "-s", HOT_URL], stdout=subprocess.DEVNULL)
        count += 1
    print(f"Issued ~{count} requests to {HOT_URL}")

def main():
    try:
        import scalene  # noqa: F401
        print("Running scalene for ~10s while issuing requests...")
        p = subprocess.Popen(["python", "-m", "scalene", __file__, "--child"])
        p.wait()
    except Exception:
        print("scalene not installed; running quick curl burst only. For flamegraph use py-spy record --pid <pid>.")
        run_curl_bomb(5)

if __name__ == "__main__":
    if os.getenv("CHILD"):  # internal recursion for scalene child exec
        run_curl_bomb(10)
    else:
        main()


