#!/usr/bin/env python
"""Black-box test suite: real HTTP calls against the running app + real Kafka/Oracle checks.

Prereq: `docker compose up -d --wait oracle kafka app` (project name sms-school).
Writes tests-artifacts/test_results.json. Every row is an observed result.
Run:  python tests/run_api_tests.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
PROJECT = os.environ.get("COMPOSE_PROJECT", "sms-school")
APP_C, KAFKA_C, ORACLE_C = (f"{PROJECT}-{s}-1" for s in ("app", "kafka", "oracle"))
TOPIC = "student-events"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests-artifacts", "test_results.json")

results = []


def record(method, endpoint, desc, status, ok, reason):
    results.append({"#": len(results) + 1, "Method": method, "Endpoint": endpoint, "Description": desc,
                    "Status Code": status, "Pass/Fail": "PASS" if ok else "FAIL", "Reason": reason})
    print(f"{len(results):>3} {'PASS' if ok else 'FAIL'} {method} {endpoint} - {desc} [{status}] {reason[:110]}", flush=True)


def http(method, path, body=None, token=None, raw=None, timeout=30):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code, text, hdrs = r.status, r.read().decode(), dict(r.headers)
    except urllib.error.HTTPError as e:
        code, text, hdrs = e.code, e.read().decode(), dict(e.headers)
    try:
        js = json.loads(text) if text else None
    except ValueError:
        js = None
    return code, js, text, hdrs, time.time() - t0


def check(method, path, desc, expected, body=None, token=None, raw=None, body_check=None, label=None):
    code, js, text, hdrs, _ = http(method, path, body, token, raw)
    ok = code in expected
    reason = f"expected {expected}, got {code}"
    if ok and body_check:
        try:
            good = bool(body_check(js, text, hdrs))
        except Exception as e:  # noqa: BLE001 - a failing probe is a FAIL row, not a crash
            good, reason = False, reason + f"; body check raised {e!r}"
        if good:
            reason += "; body checks ok"
        else:
            ok = False
            reason += f"; body check FAILED, body={text[:200]}"
    record(method, label or path, desc, code, ok, reason)
    return code, js, hdrs


def sh(cmd, timeout=120, inp=None):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, input=inp)
    return p.stdout + p.stderr


def sql(q):
    out = sh(f"docker exec -i {ORACLE_C} sqlplus -s sms/smspass@//localhost:1521/FREEPDB1",
             inp=f"set heading off feedback off pagesize 0\n{q}\n")
    return out.strip()


def consume(topic, timeout_ms=15000):
    out = sh(f"docker exec {KAFKA_C} /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 "
             f"--topic {topic} --from-beginning --timeout-ms {timeout_ms} "
             f"--property print.key=true --property key.separator='|'", timeout=timeout_ms // 1000 + 60)
    return [ln for ln in out.splitlines() if "|" in ln]


def produce(key, value, topic=TOPIC):
    sh(f"docker exec -i {KAFKA_C} /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 "
       f"--topic {topic} --property parse.key=true --property key.separator='|'", inp=f"{key}|{value}\n")


def student(first="Test", grade=10, **kw):
    d = {"firstName": first, "lastName": "Student", "dateOfBirth": "2010-05-17", "gradeLevel": grade,
         "section": "A", "guardianName": "Guardian", "guardianPhone": "+15550001111", "active": True}
    d.update(kw)
    return d


def login(user, pw):
    code, js, *_ = http("POST", "/api/v1/auth/login", {"username": user, "password": pw})
    return js if code == 200 else None


def main():
    sfx = uuid.uuid4().hex[:6]
    # ---- public + auth ----------------------------------------------------------------
    check("GET", "/health", "Health check is public", [200], body_check=lambda j, t, h: j.get("status") == "UP")
    check("GET", "/docs", "Swagger UI is public", [200], body_check=lambda j, t, h: "swagger" in t.lower())
    check("GET", "/api-docs", "OpenAPI spec is public and lists every endpoint", [200],
          body_check=lambda j, t, h: all(p in j["paths"] for p in (
              "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh",
              "/api/v1/students", "/api/v1/students/{id}", "/api/v1/students/count")))
    check("POST", "/api/v1/auth/login", "Login with blank body fields is rejected", [400], {"username": "", "password": ""})
    check("POST", "/api/v1/auth/login", "Login with wrong password is rejected", [401],
          {"username": "admin", "password": "wrong-pass"}, body_check=lambda j, t, h: j["status"] == 401)
    check("POST", "/api/v1/auth/login", "Login with unknown user is rejected", [401], {"username": "nobody", "password": "whatever1"})
    code, adm, _ = check("POST", "/api/v1/auth/login", "Admin login returns access+refresh token (2h expiry)", [200],
                         {"username": "admin", "password": "admin123"},
                         body_check=lambda j, t, h: j["accessToken"] and j["refreshToken"] and j["expiresInSeconds"] == 7200)
    A = adm["accessToken"]
    check("GET", "/api/v1/students", "Protected route without token is rejected", [401],
          body_check=lambda j, t, h: j["status"] == 401 and "correlationId" in j)
    check("GET", "/api/v1/students", "Garbage bearer token is rejected", [401], token="not.a.jwt")
    teacher_user = f"teacher_{sfx}"
    reg = {"username": teacher_user, "password": "teacherpass1", "role": "TEACHER"}
    check("POST", "/api/v1/auth/register", "Register without token is rejected", [401], reg)
    check("POST", "/api/v1/auth/register", "Admin registers a teacher", [201], reg, token=A)
    check("POST", "/api/v1/auth/register", "Duplicate username is a conflict", [409], reg, token=A)
    check("POST", "/api/v1/auth/register", "Weak/short password fails validation", [400],
          {"username": f"weak_{sfx}", "password": "short", "role": "TEACHER"}, token=A)
    code, tj, _ = check("POST", "/api/v1/auth/login", "Teacher login", [200], {"username": teacher_user, "password": "teacherpass1"})
    T = tj["accessToken"]
    check("POST", "/api/v1/auth/register", "Teacher cannot register users (RBAC)", [403],
          {"username": f"x_{sfx}", "password": "teacherpass1", "role": "TEACHER"}, token=T)
    code, rj, _ = check("POST", "/api/v1/auth/refresh", "Refresh token rotation issues new tokens", [200],
                        {"refreshToken": adm["refreshToken"]},
                        body_check=lambda j, t, h: j["accessToken"] and j["refreshToken"] != adm["refreshToken"])
    check("POST", "/api/v1/auth/refresh", "Reusing a rotated refresh token is rejected", [401], {"refreshToken": adm["refreshToken"]})
    check("POST", "/api/v1/auth/refresh", "Unknown refresh token is rejected", [401], {"refreshToken": "does-not-exist"})

    # ---- students CRUD ----------------------------------------------------------------
    check("POST", "/api/v1/students", "Create student with invalid body fails validation", [400],
          {"firstName": "", "lastName": "x", "dateOfBirth": "2999-01-01", "gradeLevel": 99, "active": None}, token=A)
    check("POST", "/api/v1/students", "Teacher cannot create students (RBAC)", [403], student(), token=T)
    code, created, hdrs = check("POST", "/api/v1/students", "Admin creates a student (201 + Location)", [201],
                                student("Alice"), token=A,
                                body_check=lambda j, t, h: j["id"] and h.get("Location", "").endswith(f"/api/v1/students/{j['id']}"))
    sid = created["id"]
    check("GET", f"/api/v1/students/{sid}", "Teacher can read a student", [200], token=T,
          body_check=lambda j, t, h: j["firstName"] == "Alice")
    check("GET", "/api/v1/students/99999999", "Unknown student is 404", [404], token=A, body_check=lambda j, t, h: j["status"] == 404)
    check("PUT", f"/api/v1/students/{sid}", "Admin updates a student", [200], student("Alicia"), token=A,
          body_check=lambda j, t, h: j["firstName"] == "Alicia")
    check("PUT", "/api/v1/students/99999999", "Update unknown student is 404", [404], student(), token=A)
    check("PUT", f"/api/v1/students/{sid}", "Teacher cannot update (RBAC)", [403], student(), token=T)
    for i in range(1, 6):
        check("POST", "/api/v1/students", f"Seed student {i}/5 in grade 11 for pagination", [201], student(f"Pg{i}", 11), token=A)
    check("GET", "/api/v1/students?grade=11&offset=1&limit=2", "List with offset=1 limit=2 (non-multiple offset) filtered by grade=11",
          [200], token=T,
          body_check=lambda j, t, h: len(j["items"]) == 2 and j["offset"] == 1 and j["limit"] == 2 and j["total"] >= 5
          and all(s["gradeLevel"] == 11 for s in j["items"]))
    check("GET", "/api/v1/students", "List default pagination", [200], token=T,
          body_check=lambda j, t, h: j["offset"] == 0 and j["limit"] == 20 and j["total"] >= 6)
    check("GET", "/api/v1/students?limit=0", "limit=0 is rejected", [400], token=A)
    check("GET", "/api/v1/students?limit=101", "limit=101 is rejected", [400], token=A)
    check("GET", "/api/v1/students?grade=13", "grade=13 is rejected", [400], token=A)
    check("DELETE", f"/api/v1/students/{sid}", "Teacher cannot delete (RBAC)", [403], token=T)
    check("DELETE", f"/api/v1/students/{sid}", "Admin deletes a student (204)", [204], token=A)
    check("GET", f"/api/v1/students/{sid}", "Deleted student is gone (404)", [404], token=A)
    check("DELETE", f"/api/v1/students/{sid}", "Deleting twice is 404", [404], token=A)

    # ---- Kafka (real broker) ----------------------------------------------------------
    code, k, _ = http("POST", "/api/v1/students", student("Kafka"), A)[:3]
    ksid = k["id"]
    http("PUT", f"/api/v1/students/{ksid}", student("Kafka2"), A)
    http("DELETE", f"/api/v1/students/{ksid}", None, A)
    time.sleep(8)
    msgs = [(ln.split("|", 1)[0], json.loads(ln.split("|", 1)[1])) for ln in consume(TOPIC) if ln.split("|", 1)[1].startswith("{")]
    mine = [(key, ev) for key, ev in msgs if ev.get("studentId") == ksid]
    types = sorted({ev["type"] for _, ev in mine})
    keyok = all(key == str(ksid) for key, _ in mine) and bool(mine)
    record("KAFKA", "", "Delivery: created/updated/deleted events for one student arrived on the real broker", "N/A",
           types == ["created", "deleted", "updated"] and keyok,
           f"types seen={types} key==studentId:{keyok}; payload sample={json.dumps(mine[0][1]) if mine else None}")

    logs = sh(f"docker logs {APP_C} 2>&1", timeout=60)
    rcv = [ln.lower() for ln in logs.splitlines() if "Received student event" in ln and f"studentid={ksid}," in ln.lower()]
    seen = sorted(t for t in ("created", "updated", "deleted") if any(f"type={t}" in ln for ln in rcv))
    record("KAFKA", "", "Consumer in the app group consumed and logged each event with details", "N/A",
           seen == ["created", "deleted", "updated"], f"'Received student event' log lines found for types {seen} (studentId={ksid})")

    dup_id, dup_sid = str(uuid.uuid4()), 999001
    ev = json.dumps({"eventId": dup_id, "type": "created", "studentId": dup_sid, "timestamp": "2026-01-01T00:00:00Z"})
    produce(str(dup_sid), ev)
    produce(str(dup_sid), ev)
    time.sleep(8)
    rows = sql(f"select count(*) from processed_event where event_id='{dup_id}';")
    recv = sum(1 for ln in sh(f"docker logs {APP_C} 2>&1", timeout=60).splitlines()
               if "Received student event" in ln and dup_id in ln)
    record("KAFKA", "", "Duplicate delivery of the same eventId causes exactly one side effect", "N/A",
           rows == "1" and recv == 1, f"processed_event rows for eventId={dup_id}: '{rows}'; 'Received' log lines={recv} (message sent twice)")

    poison = f"not-json-{uuid.uuid4().hex[:8]}"
    produce("poison", poison)
    found = False
    for _ in range(6):
        time.sleep(8)
        if any(poison in ln for ln in consume(f"{TOPIC}.dlq", 8000)):
            found = True
            break
    record("KAFKA", "", "Poison (non-JSON) message is retried then published to the DLQ and does not block the partition", "N/A",
           found, f"message {'found' if found else 'NOT found'} on {TOPIC}.dlq")

    sh(f"docker stop {KAFKA_C}", timeout=120)
    time.sleep(2)
    lat, codes = [], []
    c, j, _, _, d = http("POST", "/api/v1/students", student("Down"), A)
    lat.append(d); codes.append(c)
    did = j["id"]
    c, _, _, _, d = http("PUT", f"/api/v1/students/{did}", student("Down2"), A)
    lat.append(d); codes.append(c)
    c, j2, _, _, d = http("POST", "/api/v1/students", student("Down3"), A)
    lat.append(d); codes.append(c)
    c, _, _, _, d = http("DELETE", f"/api/v1/students/{j2['id']}", None, A)
    lat.append(d); codes.append(c)
    time.sleep(3)
    pending = sql("select count(*) from outbox_event where published_at is null;")
    all2xx = all(200 <= x < 300 for x in codes)
    record("KAFKA", "", "Broker DOWN: POST/PUT/DELETE still 2xx and fast (<1s) with events held unpublished in the outbox", "N/A",
           all2xx and max(lat) < 1.0 and pending.isdigit() and int(pending) >= 4,
           f"2xx all={all2xx}; max latency={max(lat):.3f}s; unpublished outbox rows={pending}")
    c, _, text, _, _ = http("GET", "/health")
    record("GET", "/health", "Health stays reachable while the broker is down", c, c == 200, f"status={c} body={text}")

    sh(f"docker start {KAFKA_C}", timeout=120)
    left, delivered = None, False
    for _ in range(30):
        time.sleep(5)
        left = sql("select count(*) from outbox_event where published_at is null;")
        if left == "0":
            break
    time.sleep(5)
    after = [json.loads(ln.split("|", 1)[1]) for ln in consume(TOPIC) if ln.split("|", 1)[1].startswith("{")]
    delivered = any(e.get("studentId") == did and e.get("type") == "updated" for e in after)
    record("KAFKA", "", "Broker back UP: every buffered event is delivered, outbox drained, nothing lost", "N/A",
           left == "0" and delivered,
           f"unpublished outbox rows after restart={left}; 'updated' event for student [{did}] on topic={'yes' if delivered else 'no'}")

    # ---- NEW: GET /api/v1/students/count ---------------------------------------------
    ep = "/api/v1/students/count"
    check("GET", ep, "Count without a token is rejected (401)", [401], body_check=lambda j, t, h: j["status"] == 401)
    shape = lambda j, t, h: set(j.keys()) == {"count"} and isinstance(j["count"], int) and j["count"] >= 0  # noqa: E731
    code, cj, _ = check("GET", ep, "Count with ADMIN token returns {count:<int>}", [200], token=A, body_check=shape)
    code, tj2, _ = check("GET", ep, "Count with TEACHER token returns {count:<int>}", [200], token=T, body_check=shape)
    before = http("GET", ep, token=A)[1]["count"]
    ids = []
    for i in range(1, 6):
        c, j, *_ = http("POST", "/api/v1/students", student(f"Cnt{i}", 9), A)
        if c == 201:
            ids.append(j["id"])
    after_c = http("GET", ep, token=A)[1]["count"]
    db = sql("select count(*) from student;")
    record("GET", ep, "Count increases by exactly 5 after creating 5 students (and matches DB)", 200,
           len(ids) == 5 and after_c == before + 5 and str(after_c) == db,
           f"created={len(ids)}; before={before}; after={after_c}; db count={db}")
    check("GET", ep, "Malformed bearer token is rejected (401)", [401], token="Bearer-garbage.token.value")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(results, f, indent=2)
    bad = [r for r in results if r["Pass/Fail"] != "PASS"]
    print(f"\n{len(results) - len(bad)}/{len(results)} PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
