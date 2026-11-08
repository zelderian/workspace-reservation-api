import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def request(method, url, data=None, headers=None, form=False):
    headers = dict(headers or {})
    body = None
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            if "json" not in resp.headers.get("Content-Type", ""):
                return resp.status, raw.decode(errors="replace")
            return resp.status, json.loads(raw or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def check(name, condition, details=""):
    print(f"[{'OK' if condition else 'FAIL'}] {name} {details}")
    if not condition:
        sys.exit(1)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base = (args[0] if args else "http://localhost:8000").rstrip("/")
    expect_production = "--expect-production" in sys.argv

    status, body = request("GET", f"{base}/health/db")
    check("GET /health/db", status == 200, str(body))

    status, body = request("GET", f"{base}/info")
    expected_env = "production" if expect_production else "sandbox"
    check("Середовище", status == 200 and body["env"] == expected_env, str(body))

    status, body = request("GET", f"{base}/")
    check("Головна сторінка (HTML)", status == 200 and "<html" in body.lower())

    status, _ = request("GET", f"{base}/docs")
    if expect_production:
        check("Swagger вимкнено у production", status == 404, f"status={status}")

    email = f"smoke{int(time.time() * 1000)}@example.com"
    password = "SmokePass123"
    status, body = request(
        "POST",
        f"{base}/auth/register",
        {"email": email, "full_name": "Smoke Test", "password": password},
    )
    check("POST /auth/register", status == 201, f"status={status}")

    status, body = request(
        "POST",
        f"{base}/auth/login",
        {"username": email, "password": password},
        form=True,
    )
    check("POST /auth/login", status == 200, f"status={status}")
    token = body["access_token"]

    status, body = request(
        "GET", f"{base}/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    check("GET /users/me", status == 200 and body["email"] == email)

    status, _ = request("GET", f"{base}/users/me")
    check("Анонімний доступ -> 401", status == 401, f"status={status}")
    print("Усі перевірки пройдено")


if __name__ == "__main__":
    main()
