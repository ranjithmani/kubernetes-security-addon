#!/usr/bin/env python3
"""
Safe kube-apiserver manifest patcher.
Uses yaml load/modify/dump to avoid any indentation issues.
"""

import sys
import yaml
import shutil
from datetime import datetime

MANIFEST_PATH = "/etc/kubernetes/manifests/kube-apiserver.yaml"
BACKUP_PATH   = f"/etc/kubernetes/manifests/kube-apiserver.yaml.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"

def patch_manifest(enc_config_path):
    # --- Backup first ---
    shutil.copy2(MANIFEST_PATH, BACKUP_PATH)
    print(f"✅ Backup written to {BACKUP_PATH}")

    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    container = manifest["spec"]["containers"][0]

    # --- 1. Add the flag to command ---
    flag = f"--encryption-provider-config={enc_config_path}"
    commands = container.setdefault("command", [])
    if flag not in commands:
        commands.append(flag)
        print(f"✅ Added flag: {flag}")
    else:
        print(f"ℹ️  Flag already present, skipping")

    # --- 2. Add volumeMount ---
    mount = {
        "mountPath": "/etc/kubernetes/enc",
        "name":      "enc-config",
        "readOnly":  True
    }
    mounts = container.setdefault("volumeMounts", [])
    if not any(m.get("name") == "enc-config" for m in mounts):
        mounts.append(mount)
        print("✅ Added volumeMount")
    else:
        print("ℹ️  volumeMount already present, skipping")

    # --- 3. Add volume ---
    volume = {
        "hostPath": {
            "path": "/etc/kubernetes/enc",
            "type": "DirectoryOrCreate"
        },
        "name": "enc-config"
    }
    volumes = manifest["spec"].setdefault("volumes", [])
    if not any(v.get("name") == "enc-config" for v in volumes):
        volumes.append(volume)
        print("✅ Added volume")
    else:
        print("ℹ️  Volume already present, skipping")

    # --- Write back ---
    with open(MANIFEST_PATH, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)

    print("✅ Manifest written successfully")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch_apiserver.py <enc_config_path>")
        sys.exit(1)
    patch_manifest(sys.argv[1])