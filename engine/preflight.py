"""Run first in every PRODUCTION step. Checks ElevenLabs reachability + key, prints one plain-English line.
Key source: env ELEVENLABS_API_KEY (set in the cloud environment settings), else ~/.kat/key. Exit 0 = ok."""
import os, sys, urllib.request, urllib.error

key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
if not key and os.path.exists(os.path.expanduser("~/.kat/key")):
    key = open(os.path.expanduser("~/.kat/key")).read().strip()
if len(key) < 20:
    sys.exit("PREFLIGHT FAIL: no full ElevenLabs key (set ELEVENLABS_API_KEY in the environment settings).")
try:
    urllib.request.urlopen(urllib.request.Request("https://api.elevenlabs.io/v1/user", headers={"xi-api-key": key}), timeout=30)
except urllib.error.HTTPError as e:
    sys.exit(f"PREFLIGHT FAIL: ElevenLabs rejected the key (HTTP {e.code}); the key is wrong, expired or out of credits.")
except Exception as e:
    sys.exit(f"PREFLIGHT FAIL: cannot reach api.elevenlabs.io ({e}); allow it in the environment's Network access.")
print("PREFLIGHT OK")
