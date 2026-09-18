import json
import time
import uuid
import urllib.request
from pathlib import Path

tok = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(
            "http://127.0.0.1:8001/api/auth/login",
            data=json.dumps(
                {"email": "admin@test.com", "password": "Admin@123"}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
    ).read()
)["access_token"]

sample = Path("uploads") / "demo_scan3.txt"
sample.write_text(
    "Contact Priya Kapoor at priya.kapoor@infosys.com or +91 9876543210. "
    "She works at Microsoft Azure in Mumbai. PAN ABCDE1234F.",
    encoding="utf-8",
)

boundary = "----B" + uuid.uuid4().hex
parts = []


def fld(name, value):
    parts.append(f"--{boundary}".encode())
    parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
    parts.append(b"")
    parts.append(str(value).encode())


def fl(name, path: Path):
    parts.append(f"--{boundary}".encode())
    parts.append(
        f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"'.encode()
    )
    parts.append(b"Content-Type: text/plain")
    parts.append(b"")
    parts.append(path.read_bytes())


fld("job_name", "Demo Scan 3")
fld("relative_paths_json", json.dumps([sample.name]))
fl("files", sample)
parts.append(f"--{boundary}--".encode())
parts.append(b"")
payload = b"\r\n".join(parts)

batch = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(
            "http://127.0.0.1:8001/api/batches/upload-files",
            data=payload,
            headers={
                "Authorization": "Bearer " + tok,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        ),
        timeout=120,
    ).read()
)
print("batch", batch["id"])
bid = batch["id"]

for _ in range(90):
    prog = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:8001/api/batches/{bid}/progress",
                headers={"Authorization": "Bearer " + tok},
            ),
            timeout=120,
        ).read()
    )
    print(prog)
    if prog.get("done"):
        break
    time.sleep(5)

ents = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(
            f"http://127.0.0.1:8001/api/batches/{bid}/entities",
            headers={"Authorization": "Bearer " + tok},
        ),
        timeout=60,
    ).read()
)
print("count", len(ents))
for e in ents:
    print(e["label"], e["text"], round(e["score"], 3), e["source"])
