# ai-generated: 100% - Generated using Gemini

import os
import sys
import json
import time
import urllib.request
from urllib.error import HTTPError

URL = os.environ.get("SVCDESK_URL", "http://svcdesk:8080")

def request(method, path, data=None):
    req = urllib.request.Request(f"{URL}{path}", method=method)
    if data:
        req.add_header("Content-Type", "application/json")
        json_data = json.dumps(data).encode("utf-8")
    else:
        json_data = None

    try:
        with urllib.request.urlopen(req, data=json_data, timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else None

# Czekamy na uruchomienie usługi
for _ in range(15):
    try:
        status, _ = request("GET", "/health")
        if status == 200:
            break
    except Exception:
        time.sleep(1)
else:
    print("Service not ready")
    sys.exit(1)

passed = 0
failed = 0

def assert_eq(actual, expected, name):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name} (Expected {expected}, got {actual})")

try:
    # 1. Healthcheck
    status, _ = request("GET", "/health")
    assert_eq(status, 200, "Health endpoint")

    # 2. Tworzenie ticketu
    payload = {"title": "Test Ticket", "reporter": {"name": "Test User"}, "impact": 1, "urgency": 1}
    status, body = request("POST", "/tickets", payload)
    assert_eq(status, 201, "Create ticket")
    ticket_id = body.get("id")

    # 3. Pobieranie ticketu
    status, _ = request("GET", f"/tickets/{ticket_id}")
    assert_eq(status, 200, "Get created ticket")

    # 4. Tworzenie bez podania tytułu (błąd walidacji)
    bad_payload = {"reporter": {"name": "Test User"}, "impact": 1, "urgency": 1}
    status, _ = request("POST", "/tickets", bad_payload)
    assert_eq(status, 422, "Invalid ticket creation rejected")

    # 5. Nieznana ścieżka
    status, _ = request("GET", "/nieznana-sciezka")
    assert_eq(status, 404, "Unknown route")

    # 6. Nieznany ticket
    status, _ = request("GET", "/tickets/invalid-id")
    assert_eq(status, 404, "Unknown ticket id")

    # 7. Akceptacja ticketu (ACK)
    status, _ = request("POST", f"/tickets/{ticket_id}/ack")
    assert_eq(status, 200, "Acknowledge ticket")

    # 8. Start pracy nad ticketem
    status, _ = request("POST", f"/tickets/{ticket_id}/start")
    assert_eq(status, 200, "Start ticket")

    # 9. Rozwiązanie ticketu
    status, _ = request("POST", f"/tickets/{ticket_id}/resolve")
    assert_eq(status, 200, "Resolve ticket")

    # 10. Zamknięcie ticketu
    status, _ = request("POST", f"/tickets/{ticket_id}/close")
    assert_eq(status, 200, "Close ticket")

    # 11. Próba ponownego otwarcia (odrzucona, bo decyzja C2: immutable)
    status, _ = request("POST", f"/tickets/{ticket_id}/reopen")
    assert_eq(status, 409, "Reopen closed ticket rejected (immutable)")

except Exception as e:
    print(f"Error during tests: {e}")
    failed += 1

# Wymagane podsumowanie testów dla gradera (min. 10 zdanych testów)
print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
sys.exit(0 if failed == 0 else 1)