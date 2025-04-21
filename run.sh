#!/bin/bash

# Run script for STLman after initial setup

# Load share config
CONFIG_FILE="$(dirname "$0")/mount.conf"
if [ -f "$CONFIG_FILE" ]; then
	source "$CONFIG_FILE"
else
	echo "❌ Config file not found: $CONFIG_FILE"
	exit 1
fi

# Ensure mount point exists
if [ ! -d "$MOUNT_POINT" ]; then
	echo "📁 Creating mount point at $MOUNT_POINT"
	sudo mkdir -p "$MOUNT_POINT"
fi

# Check if already mounted
if mountpoint -q "$MOUNT_POINT"; then
	echo "✅ Network share already mounted at $MOUNT_POINT"
else
	read -p "🔐 Enter username for share (default: guest): " SHARE_USER
	SHARE_USER=${SHARE_USER:-guest}  # default to guest if blank

	if [ "$SHARE_USER" != "guest" ]; then
		read -s -p "🔑 Enter password: " SHARE_PASS
		echo ""
		MOUNT_OPTIONS="username=$SHARE_USER,password=$SHARE_PASS,uid=$(id -u),gid=$(id -g),rw"
	else
		MOUNT_OPTIONS="guest,uid=$(id -u),gid=$(id -g),rw"
	fi

	echo "🔌 Attempting to mount $SHARE to $MOUNT_POINT..."
	sudo mount -t cifs "$SHARE" "$MOUNT_POINT" -o "$MOUNT_OPTIONS"

	if mountpoint -q "$MOUNT_POINT"; then
		echo "✅ Mounted successfully."
	else
		echo "❌ Failed to mount network share. Please check credentials or network."
		read -p "❓ Continue anyway? (y/N): " continue_flag
		if [[ "$continue_flag" != "y" && "$continue_flag" != "Y" ]]; then
			echo "🚫 Exiting script."
			exit 1
		else
			echo "⚠️ Continuing without mounted share. Some features may not work."
		fi
	fi
fi

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
APP_MODULE="stlman"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found. Run ./deploy.sh first."
    exit 1
fi

echo "✅ Activating environment and launching STLman..."
source "$VENV_DIR/bin/activate"

export FLASK_APP="$APP_MODULE"
export FLASK_ENV=development  # Change to 'production' if deploying more seriously

flask run --host=127.0.0.1 --port=5000
