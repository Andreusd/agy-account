#!/usr/bin/env python3
import sys
import os
import json
import base64
import shutil
import subprocess
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    advapi32 = ctypes.windll.advapi32

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ('Flags', wintypes.DWORD),
            ('Type', wintypes.DWORD),
            ('TargetName', wintypes.LPWSTR),
            ('Comment', wintypes.LPWSTR),
            ('LastWritten', wintypes.FILETIME),
            ('CredentialBlobSize', wintypes.DWORD),
            ('CredentialBlob', ctypes.c_char_p),
            ('Persist', wintypes.DWORD),
            ('AttributeCount', wintypes.DWORD),
            ('Attributes', ctypes.c_void_p),
            ('TargetAlias', wintypes.LPWSTR),
            ('UserName', wintypes.LPWSTR)
        ]

    PCREDENTIAL = ctypes.POINTER(CREDENTIAL)

ACCOUNTS_DIR = Path.home() / ".gemini" / "antigravity-accounts"

def _parse_target(target, default_username="antigravity"):
    if ":" in target:
        parts = target.split(":", 1)
        return parts[0], parts[1]
    return target, default_username

def _check_linux_prerequisites():
    if not shutil.which("secret-tool"):
        print("Error: 'secret-tool' command not found. Please install libsecret / libsecret-tools.")
        print("  - For Fedora / RHEL: sudo dnf install libsecret")
        print("  - For Ubuntu / Debian: sudo apt install libsecret-tools")
        print("  - For Arch Linux: sudo pacman -S libsecret")
        return False
    return True

def read_cred(target="gemini:antigravity"):
    if IS_WINDOWS:
        pcred = PCREDENTIAL()
        res = advapi32.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pcred))
        if not res:
            return None
        cred = pcred.contents
        size = cred.CredentialBlobSize
        blob = ctypes.string_at(cred.CredentialBlob, size)
        advapi32.CredFree(pcred)
        try:
            return blob.decode('utf-8')
        except Exception:
            return None
    elif IS_LINUX:
        if not _check_linux_prerequisites():
            return None
        service, username = _parse_target(target)
        try:
            res = subprocess.run(
                ["secret-tool", "lookup", "service", service, "username", username],
                capture_output=True,
                text=True,
                check=True
            )
            return res.stdout if res.stdout else None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    else:
        print(f"Error: Unsupported operating system: {sys.platform}")
        return None

def write_cred(target, username, blob_str):
    if IS_WINDOWS:
        raw_bytes = blob_str.encode('utf-8')
        cred = CREDENTIAL()
        cred.Flags = 0
        cred.Type = CRED_TYPE_GENERIC
        cred.TargetName = target
        cred.Comment = "Antigravity Account Profile"
        cred.CredentialBlobSize = len(raw_bytes)
        cred.CredentialBlob = raw_bytes
        cred.Persist = CRED_PERSIST_LOCAL_MACHINE
        cred.AttributeCount = 0
        cred.Attributes = None
        cred.TargetAlias = None
        cred.UserName = username
        
        return bool(advapi32.CredWriteW(ctypes.byref(cred), 0))
    elif IS_LINUX:
        if not _check_linux_prerequisites():
            return False
        service, target_username = _parse_target(target, default_username=username)
        label = f"Password for '{target_username}' on '{service}'"
        try:
            subprocess.run(
                ["secret-tool", "store", f"--label={label}", "service", service, "username", target_username],
                input=blob_str,
                text=True,
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    else:
        print(f"Error: Unsupported operating system: {sys.platform}")
        return False

def delete_cred(target):
    if IS_WINDOWS:
        return bool(advapi32.CredDeleteW(target, CRED_TYPE_GENERIC, 0))
    elif IS_LINUX:
        if not _check_linux_prerequisites():
            return False
        service, username = _parse_target(target)
        try:
            subprocess.run(
                ["secret-tool", "clear", "service", service, "username", username],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    else:
        return False

def extract_email(blob_str):
    try:
        data = json.loads(blob_str)
        idt = data.get('id_token')
        if not idt:
            return None
        parts = idt.split('.')
        if len(parts) >= 2:
            payload = parts[1]
            payload += '=' * (-len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload.encode()))
            return decoded.get('email')
    except Exception:
        pass
    return None

def cmd_save(alias=None):
    raw = read_cred("gemini:antigravity")
    if not raw:
        backend_name = "Windows Credential Manager" if IS_WINDOWS else "Secret Service keyring"
        print(f"Error: No active Antigravity credentials found in {backend_name}.")
        return 1
    
    email = extract_email(raw)
    if not alias:
        if email and "@" in email:
            alias = email.split("@")[0]
        else:
            alias = "default"
    
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    target_file = ACCOUNTS_DIR / f"{alias}.json"
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(raw)
    
    write_cred(f"gemini:antigravity:profile:{alias}", "antigravity", raw)
    
    print(f"Successfully saved active account profile '{alias}' ({email})")
    print(f"Stored at: {target_file}")
    return 0

def cmd_delete(alias):
    target_file = ACCOUNTS_DIR / f"{alias}.json"
    deleted = False
    if target_file.exists():
        target_file.unlink()
        deleted = True
    
    target_cred = f"gemini:antigravity:profile:{alias}"
    delete_cred(target_cred)
    
    if deleted:
        print(f"Deleted saved account profile '{alias}'.")
        return 0
    else:
        print(f"Profile '{alias}' not found.")
        return 1

def cmd_list():
    current_raw = read_cred("gemini:antigravity")
    current_email = extract_email(current_raw) if current_raw else None
    
    print("\n=== Antigravity Saved Account Profiles ===")
    if not ACCOUNTS_DIR.exists():
        print("No saved account profiles yet.")
    else:
        files = list(ACCOUNTS_DIR.glob("*.json"))
        if not files:
            print("No saved account profiles yet.")
        for f in files:
            alias = f.stem
            try:
                content = f.read_text(encoding="utf-8")
                email = extract_email(content) or "Unknown"
            except Exception:
                email = "Error reading"
            active_marker = "  <- [ACTIVE]" if current_email and email == current_email else ""
            print(f"  * {alias:15} : {email}{active_marker}")
            
    print(f"\nCurrently active: {current_email or 'None'}\n")
    return 0

def cmd_switch(target_alias):
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    target_file = ACCOUNTS_DIR / f"{target_alias}.json"
    
    if not target_file.exists():
        matched = False
        for f in ACCOUNTS_DIR.glob("*.json"):
            try:
                c = f.read_text(encoding="utf-8")
                if extract_email(c) == target_alias:
                    target_file = f
                    target_alias = f.stem
                    matched = True
                    break
            except Exception:
                pass
        if not matched:
            print(f"Error: Account profile '{target_alias}' not found in {ACCOUNTS_DIR}")
            print("Run 'agy-account list' to see available profiles.")
            return 1

    content = target_file.read_text(encoding="utf-8")
    email = extract_email(content)
    
    ok = write_cred("gemini:antigravity", "antigravity", content)
    if not ok:
        backend_name = "Windows Credential Manager" if IS_WINDOWS else "Secret Service keyring"
        print(f"Error writing credential to {backend_name}.")
        return 1
        
    ga_file = Path.home() / ".gemini" / "google_accounts.json"
    try:
        if email:
            ga_file.write_text(json.dumps({"active": email, "old": []}, indent=2), encoding="utf-8")
    except Exception:
        pass
        
    print(f"Switched active Antigravity account to: {target_alias} ({email})")
    print("Zero browser login required! The refresh token has been loaded into your credentials keyring.")
    return 0

def cmd_current():
    raw = read_cred("gemini:antigravity")
    email = extract_email(raw) if raw else None
    print(f"Active account: {email or 'None'}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: agy-account [list | save [alias] | switch <alias> | delete <alias> | current]")
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "list":
        sys.exit(cmd_list())
    elif cmd == "save":
        alias = sys.argv[2] if len(sys.argv) > 2 else None
        sys.exit(cmd_save(alias))
    elif cmd == "switch":
        if len(sys.argv) < 3:
            print("Usage: agy-account switch <alias>")
            sys.exit(1)
        sys.exit(cmd_switch(sys.argv[2]))
    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("Usage: agy-account delete <alias>")
            sys.exit(1)
        sys.exit(cmd_delete(sys.argv[2]))
    elif cmd == "current":
        sys.exit(cmd_current())
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: agy-account [list | save [alias] | switch <alias> | delete <alias> | current]")
        sys.exit(1)
