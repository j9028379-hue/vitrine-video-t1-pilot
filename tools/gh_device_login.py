"""Connexion GitHub par device flow (aucun jeton n'est écrit dans le dépôt)."""
from __future__ import annotations
import json, sys, time, urllib.parse, urllib.request

CLIENT_ID = "178c6fc778ccc68e1d6a"
SCOPE = "public_repo"
OUT = "/tmp/gh_token.txt"
CODE_FILE = "/tmp/gh_device_code.json"

def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Accept": "application/json"})
    return json.load(urllib.request.urlopen(req))

def main():
    start = post("https://github.com/login/device/code", {"client_id": CLIENT_ID, "scope": SCOPE})
    json.dump(start, open(CODE_FILE, "w"))
    print("CODE", start["user_code"], "URL", start["verification_uri"], flush=True)
    interval = int(start.get("interval", 5))
    deadline = time.time() + int(start.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        try:
            res = post("https://github.com/login/oauth/access_token",
                       {"client_id": CLIENT_ID, "device_code": start["device_code"],
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
        except Exception as exc:  # réseau
            print("retry", exc, flush=True)
            continue
        if res.get("access_token"):
            open(OUT, "w").write(res["access_token"])
            print("TOKEN_OK", flush=True)
            return
        err = res.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        print("ERR", err, res.get("error_description"), flush=True)
        return
    print("EXPIRED", flush=True)

if __name__ == "__main__":
    sys.exit(main())
