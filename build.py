"""Build the Postman collections and environments in this repo.

The JSON under collections/ and environments/ is generated from the specs
below: edit here, run `python build.py`, commit both. CI fails if they drift.
Every endpoint, parameter and response shape comes from the live docs pages
and the server code; example values are illustrative.
"""

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).parent
SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
NS = uuid.UUID("5b0c1c7e-3d2a-4a8e-9f10-2d6c7a1e0b55")

SMP_SITE = "https://singaporemobileproxy.com"
CF_SITE = "https://cloudf.one"
UTM = "utm_source=postman&utm_medium=collection"

# Runs after every request. Only checks what is true of every response on
# these APIs (JSON body), so it passes against the CI mock and the real thing.
TEST_EVENT = [{
    "listen": "test",
    "script": {"type": "text/javascript", "exec": [
        "pm.test('response is JSON', function () {",
        "    pm.response.to.have.jsonBody();",
        "});",
    ]},
}]


def _id(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))


def _url(path, query=None, path_vars=None):
    segs = [s for s in path.strip("/").split("/") if s]
    raw = "{{baseUrl}}/" + "/".join(segs)
    q = [{"key": k, "value": v, "description": d, **({"disabled": True} if off else {})}
         for k, v, d, off in (query or [])]
    live = [x for x in q if not x.get("disabled")]
    if live:
        raw += "?" + "&".join(f"{x['key']}={x['value']}" for x in live)
    url = {"raw": raw, "host": ["{{baseUrl}}"], "path": segs}
    if q:
        url["query"] = q
    if path_vars:
        url["variable"] = [{"key": k, "value": v, "description": d} for k, v, d in path_vars]
    return url


def request(coll, name, method, path, desc, *, body=None, form=None, query=None, path_vars=None,
            headers=None, examples=(), auth=None):
    req = {
        "method": method,
        "header": [{"key": k, "value": v, "description": d} for k, v, d in (headers or [])],
        "url": _url(path, query, path_vars),
        "description": desc,
    }
    if body is not None:
        req["header"].append({"key": "Content-Type", "value": "application/json"})
        req["body"] = {"mode": "raw", "raw": json.dumps(body, indent=2),
                       "options": {"raw": {"language": "json"}}}
    if form is not None:
        # multipart file fields; pick the file in Postman (src stays empty in the repo)
        req["body"] = {"mode": "formdata", "formdata": [
            {"key": k, "type": "file", "src": [], "description": d} for k, d in form]}
    if auth is not None:
        req["auth"] = auth
    item = {"id": _id(coll, name), "name": name, "request": req, "response": []}
    for ex_name, code, status, ex_body in examples:
        item["response"].append({
            "id": _id(coll, name, ex_name),
            "name": ex_name,
            "originalRequest": {k: v for k, v in req.items() if k != "description"},
            "status": status,
            "code": code,
            "_postman_previewlanguage": "json",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": json.dumps(ex_body, indent=2),
        })
    return item


def folder(name, desc, items, auth=None):
    f = {"name": name, "description": desc, "item": items}
    if auth is not None:
        f["auth"] = auth
    return f


def collection(key, name, desc, auth, variables, items):
    return {
        "info": {"_postman_id": _id(key), "name": name, "description": desc, "schema": SCHEMA},
        "auth": auth,
        "event": TEST_EVENT,
        "variable": [{"key": k, "value": v, "type": "string", "description": d} for k, v, d in variables],
        "item": items,
    }


def environment(key, name, values):
    return {
        "id": _id("env", key),
        "name": name,
        "values": [{"key": k, "value": v, "type": t, "enabled": True} for k, v, t in values],
        "_postman_variable_scope": "environment",
    }


APIKEY_AUTH = {"type": "apikey", "apikey": [
    {"key": "key", "value": "x-api-key", "type": "string"},
    {"key": "value", "value": "{{apiKey}}", "type": "string"},
    {"key": "in", "value": "header", "type": "string"},
]}


def bearer(var):
    return {"type": "bearer", "bearer": [{"key": "token", "value": "{{" + var + "}}", "type": "string"}]}


# ---------------------------------------------------------------- SMP shared

def smp_err(msg):
    return {"detail": {"message": msg}}


SMP_401 = ("401 missing or invalid key", 401, "Unauthorized", smp_err("API key is invalid."))
OS_TYPES = "android:1, android:3, android:4, ios:1, ios:2, ios:3, macosx:3, macosx:4, macosx:5, windows:1, windows:4"
LICENSE = "db4474ea-5f1e-4c2b-9a7d-3e8f6b2a1c90"
HOST = "sg.veerlane.com"


# ---------------------------------------------------------- SMP customer API

def smp_customer():
    c = "smp-customer"
    port_example = {
        "uuid": LICENSE,
        "license_status": "ACTIVE",
        "package_name": "200GB Plan",
        "host_domain": HOST,
        "http_port": 8101,
        "socket_port": 5101,
        "start_date": "2026-09-01T00:00:00+00:00",
        "expired_date": "2026-10-01T00:00:00+00:00",
        "m_type": "PROXYSMART",
        "status": "CONNECTED",
        "rotation_link": f"{SMP_SITE}/api/v1/proxy/change-ip?license={LICENSE}",
        "min_time_change_ip": 5,
        "authentication_user": "user8101:pass8101",
        "authorization_ips": "",
        "dl_bytes": "0",
        "bandwidth_limit_gb": 200.0,
        "bandwidth_used_gb": 45.2,
        "auto_extend": False,
    }
    plans = []
    for gb, month in ((200, 40.0), (500, 50.0), (1000, 85.0)):
        plans += [
            {"bandwidth_gb": gb, "price_usd": round(month * 0.1, 2), "planType": "DAY"},
            {"bandwidth_gb": gb, "price_usd": round(month / 3, 2), "planType": "WEEK"},
            {"bandwidth_gb": gb, "price_usd": month, "planType": "MONTH"},
        ]
    uuid_body = {"uuid": "{{licenseUuid}}"}

    account = folder("Account & plans", "Read-only. Safe to call at any time.", [
        request(c, "List my proxies", "GET", "proxies/my",
                "Every proxy on your account with its connection details, bandwidth used and expiry. "
                "`uuid` is the license id the other endpoints take.",
                examples=[("200 OK", 200, "OK", {"proxyList": [port_example]}), SMP_401]),
        request(c, "List plans and stock", "GET", "proxies",
                "Plans you can buy, per location, with prices for each `planType` and the number of free modems "
                "(`proxy_count`). Pass one of these `bandwidth_gb` values to a purchase.",
                examples=[("200 OK", 200, "OK", {"proxies": [{
                    "country": "Singapore", "city": "Singapore", "isp": "Mobile", "type": "PROXYSMART",
                    "proxy_count": 10, "plans": plans}]})]),
        request(c, "Get credit balance", "GET", "account/balance",
                "Account credit and the 20 most recent credit transactions.",
                examples=[("200 OK", 200, "OK", {"credits": 15.0, "transactions": [{
                    "id": "7c1d0f7e-...", "amount": 15.0, "balance_after": 15.0, "type": "promotion",
                    "description": "welcome bonus", "created_at": "2026-09-20T10:00:00+00:00"}]})]),
    ])

    billing = folder("Buy & renew (charges money)",
                     "**These spend money.** Credits are applied first; the rest is charged to the card saved on "
                     "your account. Nothing here asks for confirmation. Limit: 5 purchases an hour.", [
        request(c, "Buy a proxy", "POST", "proxy/purchase",
                "Buys new proxies. **Charges immediately.**\n\n"
                "- `country`, `city`, `isp` (required): use the values `GET /proxies` returns (`Singapore`, `Singapore`, `Mobile`).\n"
                "- `planType` (required): `DAY`, `WEEK` or `MONTH`.\n"
                "- `bandwidth_gb`: one of the tiers `GET /proxies` lists (200, 500, 1000). Default: the cheapest.\n"
                "- `quantity`: default 1.\n"
                "- `username` (`user:pass`, letters and digits) **or** `ipAddress` (IP whitelist), not both.\n"
                "- `couponCode`: optional.\n\n"
                "If some units can't be provisioned, the response says how many were created and refunds the rest to account credit.",
                body={"country": "Singapore", "city": "Singapore", "isp": "Mobile", "planType": "DAY",
                      "bandwidth_gb": 200, "quantity": 1},
                examples=[
                    ("200 OK", 200, "OK", {"message": "Success", "proxies": [{
                        "license_uuid": LICENSE, "package_name": "200GB Plan", "bandwidth_gb": 200,
                        "start_date": "2026-09-23T10:00:00+00:00", "expired_date": "2026-09-24T10:00:00+00:00",
                        "format_http": f"{HOST}:8101:user8101:pass8101",
                        "format_sock": f"{HOST}:5101:user8101:pass8101",
                        "link_change_ip": f"{SMP_SITE}/api/v1/proxy/change-ip?license={LICENSE}"}]}),
                    ("402 no card on file", 402, "Payment Required",
                     smp_err("No payment method on file. Please add a card via the web dashboard.")),
                    ("404 no free modem", 404, "Not Found",
                     {"detail": {"message": "There is no available proxy.", "refunded_usd": 4.0}}),
                ]),
        request(c, "Renew a proxy", "POST", "license/extendproxy",
                "Adds one `time_unit` (`DAY`, `WEEK` or `MONTH`) to an active license. **Charges immediately.**",
                body={"uuid": "{{licenseUuid}}", "time_unit": "MONTH"},
                examples=[("200 OK", 200, "OK", {"message": "Success", "balance": 0.0, "proxy": {
                    "modem_name": "200GB Plan", "host_domain": HOST, "http_port": 8101, "socket_port": 5101,
                    "authentication_user": "user8101:pass8101", "authorization_ips": None,
                    "start_date": "2026-09-01T00:00:00+00:00", "expired_date": "2026-10-31T00:00:00+00:00",
                    "status": "ACTIVE", "uuid": LICENSE}})]),
        request(c, "Turn auto-renew on or off", "POST", "license/autoextend",
                "`auto_extend`: `true` or `false`. Off by default. When on, the license renews from credit/card before it expires.",
                body={"uuid": "{{licenseUuid}}", "auto_extend": False},
                examples=[("200 OK", 200, "OK", {"message": "Auto-extend updated successfully."})]),
    ])

    manage = folder("Manage a proxy", "Controls for one proxy, identified by its license `uuid`.", [
        request(c, "Rotate IP", "POST", "proxy/change-ip",
                "New IP on the same host and port. 5-minute cooldown per proxy (429 with the wait in seconds).",
                body=uuid_body,
                examples=[("200 OK", 200, "OK", {"message": "Success"}),
                          ("429 cooldown", 429, "Too Many Requests",
                           smp_err("Rate limit exceeded. Try again in 212 seconds."))]),
        request(c, "Rotate IP (rotation link)", "GET", "proxy/change-ip",
                "The same rotation as a plain GET link, for tools that can only open a URL. "
                "Still needs the `x-api-key` header.",
                query=[("license", "{{licenseUuid}}", "License uuid", False)],
                examples=[("200 OK", 200, "OK", {"message": "Success"})]),
        request(c, "Reboot modem", "POST", "proxy/reboot",
                "Power-cycles the modem behind the proxy. Back in about a minute. 5-minute cooldown.",
                body=uuid_body,
                examples=[("200 OK", 200, "OK", {"message": "Reboot Device Success."})]),
        request(c, "Change authentication", "POST", "proxy/update-authentication",
                "Send one of: `userName` as `user:pass` (letters and digits), or `ipAddress` "
                "(comma-separated IPs to whitelist).",
                body={"uuid": "{{licenseUuid}}", "userName": "newuser:newpass123"},
                examples=[("200 OK", 200, "OK", {"message": "Success"})]),
        request(c, "Set OS fingerprint", "POST", "proxy/update-os",
                f"Passive OS fingerprint the proxy presents. `osType`: {OS_TYPES}.",
                body={"uuid": "{{licenseUuid}}", "osType": "windows:4"},
                examples=[("200 OK", 200, "OK", {"message": "Success"})]),
        request(c, "Set auto-rotation interval", "POST", "license/update-rotation-time",
                "Rotate the IP on a timer. `minute`: whole number, 5 or more.",
                body={"uuid": "{{licenseUuid}}", "minute": 30},
                examples=[("200 OK", 200, "OK", {"message": "Success"})]),
    ])

    desc = (
        "Customer API for [Singapore Mobile Proxy]"
        f"({SMP_SITE}/?{UTM}): dedicated 4G/5G proxies on real Singapore SIMs (Singtel or M1).\n\n"
        f"**Auth:** create a key in the [client dashboard]({SMP_SITE}/client?{UTM}), then set `apiKey` in the "
        "environment. It goes in the `x-api-key` header (set at collection level).\n\n"
        "**Base URL:** `https://singaporemobileproxy.com/api/v1`. POST bodies can be JSON or form-encoded.\n\n"
        "**Errors** are JSON: `{\"detail\": {\"message\": \"...\"}}`. 400 bad parameter, 401 bad key, "
        "402 payment needed, 403 reseller key (use the reseller collection), 404 not found, 429 rate limited "
        "(60 requests a minute, 5 purchases an hour, 5 minutes between rotations or reboots of a proxy).\n\n"
        "**Reseller accounts** use the separate *Singapore Mobile Proxy - Reseller API* collection; "
        "reseller keys are refused here.\n\n"
        f"Human docs: {SMP_SITE}/api-docs"
    )
    return collection(c, "Singapore Mobile Proxy - Customer API", desc, APIKEY_AUTH, [
        ("baseUrl", f"{SMP_SITE}/api/v1", "API root"),
        ("licenseUuid", "", "A license uuid from GET /proxies/my"),
    ], [account, billing, manage])


# ---------------------------------------------------------- SMP reseller API

# verbatim from the server's swap-trial messages
TRIAL_MESSAGES = {
    "trial_open": "This port already has a trial running. Keep it or go back first.",
    "cooldown": "This port was swapped recently. Try again later.",
    "start_failed": "The new modem didn't pass traffic, so you're still on your original modem.",
    "attempt_limit": "This trial has tried as many modems as it can. Keep the current one or go back.",
    "not_extendable": "This trial can't be extended.",
    "go_back_unavailable": "Your original modem isn't available any more.",
}

def smp_reseller():
    c = "smp-reseller"
    port = {
        "id": "3f2a9c1e-7b4d-4e8a-9c2f-1a6b5d3e8f70",
        "label": "customer 42",
        "status": "active",
        "paused": False,
        "plan": {"id": "626ec4d4-...", "name": "200GB Plan", "bandwidth_gb": 200},
        "host": HOST,
        "http_port": 8105,
        "socks_port": 5105,
        "login": "user8105",
        "password": "pass8105",
        "http": f"{HOST}:8105:user8105:pass8105",
        "socks5": f"{HOST}:5105:user8105:pass8105",
        "rotation_link": f"https://{HOST}/rotate/<token>",
        "bandwidth_limit_gb": 200.0,
        "bandwidth_used_gb": 0.0,
        "daily_cost_usd": 0.9333,
        "auto_rotate_mins": 0,
        "created_at": "2026-09-23T10:00:00+00:00",
        "end_date": "2026-09-30",
        "removed_at": "2026-10-01T00:05:00+08:00",
        "cancelled_at": None,
        "swap_trial": None,
    }
    pid = [("portId", "{{portId}}", "Port id from GET /ports")]

    def port_req(name, path, desc, body=None, examples=None):
        return request(c, name, "POST", f"ports/:portId/{path}", desc, body=body, path_vars=pid,
                       examples=examples or [("200 OK", 200, "OK", port)])

    account = folder("Account & plans", "Read-only.", [
        request(c, "Account and credit position", "GET", "account",
                "Your discount and where you stand against your monthly credit limit. A new port has to fit in "
                "`available_usd`, which already counts what your live ports will bill until month end.",
                examples=[("200 OK", 200, "OK", {
                    "shop": {"id": "fee89a06-...", "name": "yourshop"}, "discount_pct": 30, "bonus_discount_pct": 0,
                    "credit_limit_usd": 500.0, "spent_this_month_usd": 12.4, "committed_to_month_end_usd": 11.2,
                    "available_usd": 476.4, "live_ports": 1, "remaining_days_this_month": 12,
                    "billing": "No deposit. Each port bills its daily cost against your credit limit, invoiced monthly."}),
                    SMP_401,
                    ("403 not a reseller key", 403, "Forbidden", smp_err(
                        f"This API is for reseller accounts. Customer API keys use /api/v1: {SMP_SITE}/api-docs"))]),
        request(c, "Plans and stock", "GET", "plans",
                "Tiers at your reseller price (monthly and daily) and free modems per telco (Singtel, M1).",
                examples=[("200 OK", 200, "OK", {
                    "plans": [
                        {"plan_id": "626ec4d4-...", "name": "200GB Plan", "bandwidth_gb": 200, "monthly_usd": 28.0, "daily_usd": 0.9333},
                        {"plan_id": "a8765dc1-...", "name": "500GB Plan", "bandwidth_gb": 500, "monthly_usd": 35.0, "daily_usd": 1.1667}],
                    "stock": {"singtel": {"available": 8, "label": "5+"}, "m1": {"available": 3, "label": "3"}}})]),
    ])

    ports = folder("Ports", "Create, list and remove ports. Ports bill their daily cost against your credit limit "
                            "while they run and are invoiced monthly.", [
        request(c, "List ports", "GET", "ports",
                "Your ports, newest first. Panel ports show here too.",
                query=[("status", "live", "live (default), cancelled or all", False)],
                examples=[("200 OK", 200, "OK", {"ports": [port]})]),
        request(c, "Get one port", "GET", "ports/:portId", "One port, including cancelled ones.",
                path_vars=pid,
                examples=[("200 OK", 200, "OK", port),
                          ("404 not yours", 404, "Not Found", smp_err("No such port."))]),
        request(c, "Create ports (bills daily)", "POST", "ports",
                "Creates ports on your credit line. **Starts billing** its daily cost from creation.\n\n"
                "- `bandwidth_gb` (200, 500 or 1000; default the cheapest) or `plan_id`\n"
                "- `quantity`: 1-10, default 1 (limit 30 new ports an hour)\n"
                "- `days`: 1-365 sets the end date; leave out to run until cancelled\n"
                "- `telco`: `singtel` or `m1` (optional)\n"
                "- `label`: up to 64 characters\n\n"
                "A port runs through its end date (Singapore time) and is removed at 00:05 SGT the next morning.",
                body={"bandwidth_gb": 500, "days": 7, "telco": "singtel", "label": "customer 42"},
                examples=[
                    ("201 Created", 201, "Created", {"message": "Created", "requested": 1, "created": 1, "ports": [port]}),
                    ("402 over credit limit", 402, "Payment Required", {"detail": {
                        "message": "That goes past your $500.00 credit limit: 0 of 1 fit. Ask us to raise it.",
                        "available_usd": 0.4}}),
                    ("503 no free modem", 503, "Service Unavailable", smp_err(
                        "No free modem could take a port right now. Nothing was created or billed; try again shortly.")),
                ]),
        port_req("Cancel port (removes it now)", "cancel",
                 "Removes the port now and stops its billing. The port is only marked cancelled once the proxy "
                 "server confirms; otherwise you get a 502 and it stays live.",
                 examples=[("200 OK", 200, "OK", {**port, "status": "cancelled",
                                                  "cancelled_at": "2026-09-24T09:00:00+00:00"})]),
        port_req("Set end date", "end-date",
                 "Send `date` (`YYYY-MM-DD`, tomorrow to 365 days out, or `null` to clear it) **or** `add_days` "
                 "(1-365, added to the current end date, or to today if none).",
                 body={"add_days": 30}),
    ])

    manage = folder("Manage a port", "Controls for one port.", [
        port_req("Rotate IP", "rotate",
                 "New IP. 5-minute cooldown per port. Your customer can also use the port's `rotation_link`.",
                 examples=[("200 OK", 200, "OK", {"message": "Rotated"})]),
        port_req("Reboot modem", "reboot", "5-minute cooldown.",
                 examples=[("200 OK", 200, "OK", {"message": "Rebooting. The proxy is back in about a minute."})]),
        port_req("Swap modem", "swap-modem",
                 "Moves the port to another modem, e.g. when one is dead. Host, port and login stay the same. "
                 "`telco` optional: `singtel` or `m1`.", body={"telco": "m1"}),
        port_req("Change proxy login", "credentials",
                 "`login` and `password`, both required, letters and digits only, up to 64 each.",
                 body={"login": "customer42", "password": "s3cretPass"}),
        port_req("Change plan", "plan",
                 "`bandwidth_gb` or `plan_id`. An upgrade has to fit your credit limit.", body={"bandwidth_gb": 1000}),
        port_req("Set label", "label", "Empty string clears it.", body={"label": "customer 42"}),
        port_req("Set OS fingerprint", "os", f"`os_type`: none, {OS_TYPES}.", body={"os_type": "windows:4"},
                 examples=[("200 OK", 200, "OK", {"message": "Updated", "os_type": "windows:4"})]),
        port_req("Set auto-rotate", "auto-rotate", "`minutes`: 0 turns it off, otherwise 5-1440.",
                 body={"minutes": 30}),
    ])

    trial = {
        "id": "9d1c2b3a-...",
        "status": "active",
        "started_via": "api",
        "on_timeout": "keep",
        "modem": {"modem_id": "m_1a2b3c4d5e", "carrier": "m1", "model": "M300z", "tag": "482",
                  "network": "5G", "server_id": "b7e1..."},
        "credentials_change": False,
        "new_proxy": None,
        "attempts": 1,
        "started_at": "2026-10-12T10:00:00+00:00",
        "expires_at": "2026-10-12T10:10:00+00:00",
        "seconds_left": 600,
        "extended": False,
        "can_extend": True,
        "ended_at": None,
        "outcome": None,
        "can_go_back": False,
        "went_back": False,
    }
    kept = {**trial, "status": "kept", "expires_at": None, "seconds_left": 0, "can_extend": False,
            "ended_at": "2026-10-12T10:04:00+00:00", "can_go_back": True}
    reverted = {**trial, "status": "reverted", "expires_at": None, "seconds_left": 0, "can_extend": False,
                "ended_at": "2026-10-12T10:04:00+00:00"}

    def with_port(t):
        return {"trial": t, "port": {**port, "swap_trial": t}}

    def trial_err(status, phrase, code, extra=None):
        return (f"{status} {code}", status, phrase,
                {"detail": {"message": TRIAL_MESSAGES[code], "code": code, **(extra or {})}})

    no_open = ("409 no_open_trial", 409, "Conflict",
               {"detail": {"message": "This port has no trial to act on.", "code": "no_open_trial"}})
    trials = folder("Modem trials", "Move a port to another modem for 10 minutes, then keep it or go back. "
                                    "Built for a customer who says their line is slow. A trial on the same server "
                                    "never changes host, port or login; one on another server does "
                                    "(`credentials_change: true`, test with `new_proxy` until you keep it). "
                                    "Errors carry `detail.code`.", [
        request(c, "Swap options", "GET", "ports/:portId/swap-options",
                "Every free modem this port could move to, by server: carrier, model, 4G/5G, signal, last measured "
                "speed and today's speed-test pass count. Pass a card's `modem_id` to start a trial.",
                path_vars=pid,
                examples=[("200 OK", 200, "OK", {
                    "current": {"server_id": "b7e1...", "server_name": "Server 3", "model": "E3372", "tag": "917",
                                "network": "4G", "telco": "singtel", "telco_label": "Singtel"},
                    "cross_server_enabled": True,
                    "servers": [{"server_id": "b7e1...", "name": "Server 3", "is_current": True, "unavailable": False,
                                 "modems": [{"modem_id": "m_1a2b3c4d5e", "server_id": "b7e1...", "telco": "m1",
                                             "telco_label": "M1", "model": "M300z", "tag": "482", "network": "5G",
                                             "signal": 4, "down_mbps": 182.4, "up_mbps": 31.2, "latency_ms": 28,
                                             "tested_at": "2026-10-12T08:00:00+00:00", "tests_ok_24h": 6,
                                             "tests_total_24h": 6}]}],
                    "trial": None, "trial_minutes": 10, "extend_minutes": 10, "go_back_minutes": 60})]),
        port_req("Start a trial", "swap-trial",
                 "Moves the port onto another modem for 10 minutes. Send `modem_id` from swap-options, or "
                 "`telco` (`singtel` or `m1`) and/or `server_id` to let us pick. `on_timeout`: `keep` (default) "
                 "or `revert`, what happens if you do nothing.",
                 body={"modem_id": "m_1a2b3c4d5e", "on_timeout": "keep"},
                 examples=[("200 OK", 200, "OK", with_port(trial)),
                           trial_err(409, "Conflict", "trial_open"),
                           trial_err(429, "Too Many Requests", "cooldown",
                                     {"available_at": "2026-10-12T10:30:00+00:00"}),
                           trial_err(503, "Service Unavailable", "start_failed")]),
        request(c, "Current trial", "GET", "ports/:portId/swap-trial",
                "The port's open trial, or one that ended in the last hour.",
                path_vars=pid,
                examples=[("200 OK", 200, "OK", {"trial": trial}),
                          ("404 no_recent_trial", 404, "Not Found", {"detail": {
                              "message": "This port has no trial in the last hour.", "code": "no_recent_trial"}})]),
        port_req("Keep the new modem", "swap-trial/keep", "Ends the trial on the new modem.",
                 examples=[("200 OK", 200, "OK", with_port(kept)), no_open]),
        port_req("Revert to the original modem", "swap-trial/revert", "Ends the trial back on the original modem.",
                 examples=[("200 OK", 200, "OK", with_port(reverted)), no_open]),
        port_req("Try another modem", "swap-trial/next",
                 "Stays in the same trial and moves to another modem. Same body as starting one.",
                 body={"modem_id": "m_6f7e8d9c0b"},
                 examples=[("200 OK", 200, "OK", with_port({**trial, "attempts": 2})), no_open,
                           trial_err(429, "Too Many Requests", "attempt_limit")]),
        port_req("Extend by 10 minutes", "swap-trial/extend", "Once per trial.",
                 examples=[("200 OK", 200, "OK", with_port({**trial, "extended": True, "can_extend": False,
                                                           "seconds_left": 1080})),
                           trial_err(409, "Conflict", "not_extendable")]),
        port_req("Go back after keeping", "swap-trial/go-back",
                 "Undoes a same-server keep within an hour, if the original modem is still free.",
                 examples=[("200 OK", 200, "OK", with_port({**kept, "can_go_back": False, "went_back": True})),
                           trial_err(409, "Conflict", "go_back_unavailable")]),
    ])

    desc = (
        "Reseller API for [Singapore Mobile Proxy]"
        f"({SMP_SITE}/?{UTM}): create and manage dedicated Singapore mobile proxies (Singtel or M1) for your own "
        "customers, at your reseller price.\n\n"
        "**Auth:** make a key in the reseller dashboard (`/shop/api-keys`), set `apiKey` in the environment. "
        "Sent as `x-api-key`. Customer keys are refused here, and reseller keys on the customer API.\n\n"
        "**Billing:** no deposit. Each port bills its daily cost against your monthly credit limit ($500 by default) "
        "and you're invoiced monthly.\n\n"
        "**Errors:** `{\"detail\": {\"message\": \"...\"}}`. 400 bad parameter, 401 bad key, 402 past your credit "
        "limit, 403 not a reseller key / account inactive, 404 no such port, 409 port cancelled or a trial "
        "conflict (see `detail.code`), 429 too fast "
        "(120 requests a minute, 30 new ports an hour, 5 minutes between rotations or reboots of a port), "
        "502 the proxy server refused (nothing changed), 503 no free modem (nothing created or billed).\n\n"
        f"Human docs: {SMP_SITE}/reseller-api-docs"
    )
    return collection(c, "Singapore Mobile Proxy - Reseller API", desc, APIKEY_AUTH, [
        ("baseUrl", f"{SMP_SITE}/api/reseller/v1", "API root"),
        ("portId", "", "A port id from GET /ports"),
    ], [account, ports, manage, trials])


# ------------------------------------------------------------ cloudf.one API

def cloudfone():
    c = "cloudfone"
    serial = "R58N12ABCDE"
    device = {
        "serial": serial, "present": True, "ready": True, "using": False, "owner": None,
        "manufacturer": "SAMSUNG", "model": "SM-G981B", "marketName": "Galaxy S20 5G",
        "operator": "Singtel", "version": "13", "sdk": "33", "abi": "arm64-v8a",
        "battery": {"level": 80, "status": "not_charging", "health": "good", "temp": 31.0},
        "network": {"connected": True, "type": "MOBILE", "subtype": "LTE"},
        "display": {"width": 1080, "height": 2400},
    }
    stf_401 = ("401 missing or bad token", 401, "Unauthorized",
               {"success": False, "description": "Bad Credentials"})
    serial_var = [("serial", "{{serial}}", "Device serial from GET /devices")]

    account = folder("Account", "Token healthcheck and token management.", [
        request(c, "My account", "GET", "user",
                "Email, name, privilege and group. Cheapest way to check a token works.",
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Getting user info", "user": {
                    "email": "you@example.com", "name": "you", "privilege": "user",
                    "group": "a1b2c3d4...", "settings": {}}}), stf_401]),
        request(c, "List access tokens", "GET", "user/accessTokens", "Names of your tokens (not their values).",
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Getting access tokens info", "tokens": ["ci", "laptop"]})]),
        request(c, "Create access token", "POST", "user/accessTokens",
                "Mints another token with the given `title`. You need one token first; the very first one is made "
                "in the web UI at cloudf.one/#!/settings.",
                query=[("title", "ci", "Label for the token", False)],
                examples=[("201 Created", 201, "Created", {"success": True, "description": "Created (access token)", "token": {"id": "<new token id>", "title": "ci"}})]),
        request(c, "Revoke access token", "DELETE", "user/accessTokens/:tokenId",
                "Revokes one token. It stops working immediately.",
                path_vars=[("tokenId", "{{tokenId}}", "Token id")],
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Deleted (access token)"})]),
        request(c, "Register adb public key", "POST", "user/adbPublicKeys",
                "Registers an adb public key (`~/.android/adbkey.pub`) on your account. Accepted today, but adb is "
                "**not reachable over the internet**; see the collection description.",
                body={"publickey": "QAAAAM... user@host", "title": "laptop"},
                examples=[("200 OK", 200, "OK", {"success": True})]),
    ])

    devices = folder("Devices", "Your phones. `GET /devices` is scoped to the phones on your account and returns an "
                                "empty list, not an error, if your subscription has lapsed.", [
        request(c, "List my phones", "GET", "devices",
                "The phones on your account: model, carrier (`operator`), Android version, battery, and whether "
                "each is present and ready.",
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Getting devices info", "devices": [device]}),
                          ("401 missing or bad token", 401, "Unauthorized", {"success": False, "devices": []})]),
        request(c, "Get one phone", "GET", "devices/:serial", "One device in full detail.",
                path_vars=serial_var,
                query=[("fields", "serial,model,operator,present,ready,battery", "Optional comma-separated field list", True)],
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Getting device info", "device": device})]),
        request(c, "Phones I hold the lock on", "GET", "user/devices",
                "Devices you currently hold the control lock on.",
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Getting user devices info", "devices": [{**device, "using": True}]})]),
        request(c, "Take control lock", "POST", "user/devices",
                "Takes the control lock on a device, like opening it in the browser does. Opening the same phone "
                "in a tab at the same time fights over the same lock. `timeout` is idle ms before release.",
                body={"serial": "{{serial}}", "timeout": 900000},
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Requested"})]),
        request(c, "Release control lock", "DELETE", "user/devices/:serial", "Releases the lock.",
                path_vars=serial_var,
                examples=[("200 OK", 200, "OK", {"success": True, "description": "Requested"})]),
        request(c, "Install an APK", "POST", "devices/:serial/install",
                "Uploads an app and installs it on one of your phones. Multipart field `file`: a .apk, or a split "
                "bundle (.apks, .xapk, or a zip of apks; OBB data in an .xapk is skipped). Pick the file in the "
                "body tab.\n\n"
                "Installs over an existing copy, never downgrades, and doesn't pre-grant permissions. Answers once "
                "Android has installed it. Up to 512 MB, one install per phone at a time, 30 an hour per account. "
                "On failure `detail` carries Android's own reason (e.g. INSTALL_FAILED_UPDATE_INCOMPATIBLE).",
                form=[("file", "The .apk, .apks or .xapk to install")],
                path_vars=serial_var,
                examples=[("200 OK", 200, "OK", {"success": True, "serial": serial, "package": "com.example.app",
                                                 "kind": "apk", "files": 1}),
                          ("404 not your phone", 404, "Not Found", {"success": False, "error": "not_found",
                                                                    "detail": "no such device on this account"}),
                          ("409 install already running", 409, "Conflict", {
                              "success": False, "error": "install_in_progress",
                              "detail": "another install is running on this phone"}),
                          ("413 over 512 MB", 413, "Content Too Large", {"success": False, "error": "too_large",
                                                                       "detail": "uploads are capped at 512 MB"}),
                          ("429 over 30 an hour", 429, "Too Many Requests", {
                              "success": False, "error": "rate_limited", "detail": "at most 30 installs per hour"})]),
    ])

    partner = folder(
        "Partner orders (partner key, charges credit)",
        "For partner accounts only, with a partner key we issue on request (separate from your access token). "
        "Orders spend a prepaid credit balance; top-ups are web-only. Set `partnerKey` in the environment.",
        [
            request(c, "Stock and prices", "GET", "stock",
                    "Free phones per carrier and the price per duration. Read-only.",
                    examples=[("200 OK", 200, "OK", {
                        "available": {"singtel": 3, "m1": 2, "total": 5},
                        "prices": {"1": 5.0, "7": 16.67, "30": 50.0},
                        "max_devices_per_order": 5}),
                        ("401 bad partner key", 401, "Unauthorized", {"error": "unauthorized"})]),
            request(c, "Order or renew phones (charges credit)", "POST", "orders",
                    "**Spends credit.** `duration_days`: 1, 7 or 30. `quantity`: the TOTAL number of phones you want "
                    "to hold (1-5), not an increment; ordering the number you already hold renews them. `carrier`: "
                    "optional, `singtel` or `m1`.\n\n"
                    "`Idempotency-Key` is required: retrying with the same key replays the original order instead of "
                    "buying again. Strict: 409 with the real available count if the pool can't fill it, 402 with your "
                    "balance and the price if credit won't cover it. Nothing is charged in either case.",
                    headers=[("Idempotency-Key", "{{$guid}}", "Unique per order; reuse it only to retry the same order")],
                    body={"duration_days": 30, "quantity": 2, "carrier": "singtel"},
                    examples=[
                        ("201 Created", 201, "Created", {
                            "order_id": "api-...", "replayed": False, "duration_days": 30,
                            "expires_at": "2026-10-23T10:00:00+00:00",
                            "devices": [{"serial": "R58N12ABCDE", "carrier": "singtel"},
                                        {"serial": "R58N12FGHIJ", "carrier": "singtel"}],
                            "pending": 0, "balance_after": 100.0, "charged": 100.0}),
                        ("409 not enough stock", 409, "Conflict",
                         {"error": "insufficient_stock", "available": 1, "requested": 2}),
                        ("402 not enough credit", 402, "Payment Required",
                         {"error": "insufficient_credit", "balance": 20.0, "price": 100.0}),
                        ("400 missing Idempotency-Key", 400, "Bad Request", {"error": "missing_idempotency_key"}),
                    ]),
            request(c, "My API orders", "GET", "orders",
                    "Your API orders, newest first, with what each was charged. Web purchases and top-ups are not "
                    "listed here.",
                    examples=[("200 OK", 200, "OK", {"orders": [{
                        "order_id": "api-...", "charged": 100.0, "created_at": "2026-09-23T10:00:00+00:00",
                        "note": "api order"}]})]),
        ],
        auth=bearer("partnerKey"),
    )

    desc = (
        f"REST API for [cloudf.one]({CF_SITE}/?{UTM}): real Android phones in Singapore on Singtel or M1 SIMs, "
        "rented by the day, week or month.\n\n"
        "The phone panel runs DeviceFarmer STF 2.4.1 and this is its API, scoped to the phones on your account. "
        "This collection covers the endpoints we support; the full STF spec is at "
        f"{CF_SITE}/api/v1/swagger.json, but its admin endpoints (groups, users, bookings) are restricted.\n\n"
        "**Auth:** log in, open your phone once, then go to cloudf.one/#!/settings > Access tokens and generate one. "
        "Set it as `accessToken`; it's sent as `Authorization: Bearer`. Tokens don't expire on a timer.\n\n"
        "**What the API doesn't do:** adb over the internet (the remoteConnect port isn't reachable from outside; "
        "a WireGuard tunnel is available on request), input injection or screenshots over REST (that's STF's "
        "websocket protocol), or credit top-ups (web only). APK install does work over REST: "
        "`POST /devices/{serial}/install` in the Devices folder. "
        "No published rate limit; polling /devices every few seconds is fine.\n\n"
        f"Human docs: {CF_SITE}/developers"
    )
    return collection(c, "cloudf.one - Cloud Phone API", desc, bearer("accessToken"), [
        ("baseUrl", f"{CF_SITE}/api/v1", "API root"),
        ("serial", "", "A device serial from GET /devices"),
        ("tokenId", "", "An access token id"),
    ], [account, devices, partner])


BUILDS = {
    "collections/singapore-mobile-proxy-customer-api.postman_collection.json": smp_customer,
    "collections/singapore-mobile-proxy-reseller-api.postman_collection.json": smp_reseller,
    "collections/cloudfone-api.postman_collection.json": cloudfone,
    "environments/singapore-mobile-proxy-customer.postman_environment.json": lambda: environment(
        "smp-customer", "Singapore Mobile Proxy - Customer",
        [("baseUrl", f"{SMP_SITE}/api/v1", "default"), ("apiKey", "", "secret"), ("licenseUuid", "", "default")]),
    "environments/singapore-mobile-proxy-reseller.postman_environment.json": lambda: environment(
        "smp-reseller", "Singapore Mobile Proxy - Reseller",
        [("baseUrl", f"{SMP_SITE}/api/reseller/v1", "default"), ("apiKey", "", "secret"), ("portId", "", "default")]),
    "environments/cloudfone.postman_environment.json": lambda: environment(
        "cloudfone", "cloudf.one",
        [("baseUrl", f"{CF_SITE}/api/v1", "default"), ("accessToken", "", "secret"),
         ("partnerKey", "", "secret"), ("serial", "", "default"), ("tokenId", "", "default")]),
}


def render() -> dict[str, str]:
    return {path: json.dumps(fn(), indent=2, ensure_ascii=False) + "\n" for path, fn in BUILDS.items()}


if __name__ == "__main__":
    import sys
    out = render()
    if "--check" in sys.argv:
        stale = [p for p, text in out.items()
                 if not (ROOT / p).exists() or (ROOT / p).read_text(encoding="utf-8") != text]
        if stale:
            sys.exit("out of date, run python build.py: " + ", ".join(stale))
        print("all generated files up to date")
    else:
        for p, text in out.items():
            (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / p).write_text(text, encoding="utf-8", newline="\n")
            print("wrote", p)
