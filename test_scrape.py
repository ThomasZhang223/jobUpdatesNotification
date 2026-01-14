import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

URLS = [
    "https://github.com/negarprh/Canadian-Tech-Internships-2026",
    "https://github.com/SimplifyJobs/Summer2026-Internships/tree/dev",
]

for url in URLS:
    print(f"\nTesting: {url}")

    # Without headers
    r1 = requests.get(url, timeout=30)
    print(f"  No headers:   {r1.status_code}")

    # With headers
    r2 = requests.get(url, headers=HEADERS, timeout=30)
    print(f"  With headers: {r2.status_code}")
