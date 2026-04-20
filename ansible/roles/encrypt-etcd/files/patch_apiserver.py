#!/usr/bin/env python3
"""
Safe kube-apiserver manifest patcher.
Uses ruamel.yaml to preserve original formatting exactly.
"""
import sys
import shutil
from datetime import datetime
from ruamel.yaml import YAML

MANIFEST_PATH = "/etc/kubernetes/manifests/kube-apiserver.yaml"
BACKUP_PATH   = f"/etc/kubernetes/manifests/kube-apiserver.yaml.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"

def patch_manifest(enc_config_path):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096           # prevent line wrapping
    yaml.indent(mapping=2, sequence=4, offset=2)

    # --- Backup first ---
    shutil.copy2(MANIFEST_PATH, BACKUP_PATH)
    print(f"✅ Backup written to {BACKUP_PATH}")

    with open(MANIFEST_PATH) as f:
        manifest = yaml.load(f)

    container = manifest["spec"]["containers"][0]

    # --- 1. Add the flag ---
    flag = f"--encryption-provider-config={enc_config_path}"
    commands = container["command"]
    if flag not in commands:
        commands.append(flag)
        print(f"✅ Added flag: {flag}")
    else:
        print(f"ℹ️  Flag already present, skipping")

    # --- 2. Add volumeMount ---
    mount = {"mountPath": "/etc/kubernetes/enc",
             "name": "enc-config",
             "readOnly": True}
    mounts = container["volumeMounts"]
    if not any(m.get("name") == "enc-config" for m in mounts):
        mounts.append(mount)
        print("✅ Added volumeMount")
    else:
        print("ℹ️  volumeMount already present, skipping")

    # --- 3. Add volume ---
    volume = {"hostPath": {"path": "/etc/kubernetes/enc",
                           "type": "DirectoryOrCreate"},
              "name": "enc-config"}
    volumes = manifest["spec"]["volumes"]
    if not any(v.get("name") == "enc-config" for v in volumes):
        volumes.append(volume)
        print("✅ Added volume")
    else:
        print("ℹ️  Volume already present, skipping")

    # --- Write back ---
    with open(MANIFEST_PATH, "w") as f:
        yaml.dump(manifest, f)
    print("✅ Manifest written successfully")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch_apiserver.py <enc_config_path>")
        sys.exit(1)
    patch_manifest(sys.argv[1])
