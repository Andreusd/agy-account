#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  Installing agy-account CLI Shim for Antigravity  "
echo "==================================================="

# Determine repository path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="${SCRIPT_DIR}/agy_account.py"

if [ ! -f "${TARGET_SCRIPT}" ]; then
    echo "[ERROR] Could not find agy_account.py in ${SCRIPT_DIR}"
    exit 1
fi

chmod +x "${TARGET_SCRIPT}"

# Verify secret-tool is installed
if ! command -v secret-tool &>/dev/null; then
    echo "[WARNING] 'secret-tool' (from libsecret) was not found in your PATH."
    echo "  Please install it to allow agy-account to access your keyring:"
    echo "  - Fedora / RHEL: sudo dnf install libsecret"
    echo "  - Ubuntu / Debian: sudo apt install libsecret-tools"
    echo "  - Arch Linux: sudo pacman -S libsecret"
    echo ""
fi

# Prefer ~/.local/bin if it exists or in PATH, otherwise ~/.gemini/antigravity-cli/bin
if [ -d "${HOME}/.local/bin" ] || [[ ":$PATH:" == *":${HOME}/.local/bin:"* ]]; then
    TARGET_BIN="${HOME}/.local/bin"
elif [ -d "${HOME}/.gemini/antigravity-cli/bin" ]; then
    TARGET_BIN="${HOME}/.gemini/antigravity-cli/bin"
else
    TARGET_BIN="${HOME}/.local/bin"
fi

mkdir -p "${TARGET_BIN}"

SHIM_FILE="${TARGET_BIN}/agy-account"

cat << 'EOF' > "${SHIM_FILE}"
#!/usr/bin/env bash
SCRIPT_PATH="__TARGET_SCRIPT__"
exec python3 "${SCRIPT_PATH}" "$@"
EOF

sed -i "s|__TARGET_SCRIPT__|${TARGET_SCRIPT}|g" "${SHIM_FILE}"
chmod +x "${SHIM_FILE}"

echo ""
echo "[SUCCESS] Shim successfully created at:"
echo "  ${SHIM_FILE}"
echo ""
echo "It points to:"
echo "  ${TARGET_SCRIPT}"
echo ""
if [[ ":$PATH:" != *":${TARGET_BIN}:"* ]]; then
    echo "[NOTE] Ensure ${TARGET_BIN} is in your PATH."
fi
echo "You can now use 'agy-account' from any terminal!"
echo "==================================================="
