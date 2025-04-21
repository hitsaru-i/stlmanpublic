#!/bin/bash

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
DB_DIR="$APP_DIR/database"
DB_FILE="$DB_DIR/stlman.db"
APP_MODULE="stlman"
INIT_EXPORT_SCRIPT="$APP_DIR/scripts/1B-extractor.py"
INIT_DB_SCRIPT="$APP_DIR/scripts/init_db.py"

# Load share config
CONFIG_FILE="$(dirname "$0")/mount.conf"
if [ -f "$CONFIG_FILE" ]; then
	source "$CONFIG_FILE"
else
	echo "❌ Config file not found: $CONFIG_FILE"
	exit 1
fi

echo "🔧 STLman: First-Time Deployment"

# Create required directories
mkdir -p "$DB_DIR" "$APP_DIR/scripts" "$APP_DIR/$APP_MODULE"

# Create Mount Point

# Load share config
CONFIG_FILE="$(dirname "$0")/mount.conf"
if [ -f "$CONFIG_FILE" ]; then
	source "$CONFIG_FILE"
else
	echo "❌ Config file not found: $CONFIG_FILE"
	exit 1
fi
##User Auth
read -p "🔐 Enter username for share (default: guest): " SHARE_USER
SHARE_USER=${SHARE_USER:-guest}  # default to guest if blank

if [ "$SHARE_USER" != "guest" ]; then
	read -s -p "🔑 Enter password: " SHARE_PASS
	echo ""
	MOUNT_OPTIONS="username=$SHARE_USER,password=$SHARE_PASS,uid=$(id -u),gid=$(id -g),rw"
else
	MOUNT_OPTIONS="guest,uid=$(id -u),gid=$(id -g),rw"
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

# Step 1: Virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "📂 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 2: requirements.txt
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "📝 Creating default requirements.txt..."
    cat > "$APP_DIR/requirements.txt" <<EOF
Flask==2.3.2
Flask-SQLAlchemy==3.1.1
Werkzeug==2.3.3
gunicorn==21.2.0
python-dotenv==1.0.1
EOF
fi

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# Step 3: Flask app scaffold
if [ ! -f "$APP_DIR/$APP_MODULE/__init__.py" ]; then
    echo "🛠️ Scaffolding Flask app..."
    cat > "$APP_DIR/$APP_MODULE/__init__.py" <<EOF
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/stlman.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
EOF
fi

if [ ! -f "$APP_DIR/$APP_MODULE/routes.py" ]; then
    cat > "$APP_DIR/$APP_MODULE/routes.py" <<EOF
from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return "Welcome to STLman!"
EOF
fi

# Step 4: Run Extractor
# --- Optional Zip Extraction Step ---
echo ""
read -p "🗜️  Would you like to extract ZIP files now using $INIT_EXPORT_SCRIPT? (y/N): " extract_confirm

if [[ "$extract_confirm" =~ ^[Yy]$ ]]; then
	echo "📦 Starting ZIP extraction..."
	python3 "$INIT_EXPORT_SCRIPT"
	if [[ $? -eq 0 ]]; then
		echo "✅ Extraction completed successfully."
	else
		echo "⚠️ Extraction script returned a non-zero exit code. Please check the output."
	fi
else
	echo "⏭️  Skipping ZIP extraction step."
fi



# Step 5: Database init script
if [ ! -f "$INIT_DB_SCRIPT" ]; then
    echo "🧱 Creating init_db.py..."
    cat > "$INIT_DB_SCRIPT" <<EOF
from stlman import db, create_app

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Database initialized.")
EOF
fi

# Step 6: Initialize database
if [ ! -f "$DB_FILE" ]; then
    echo "📦 Initializing database..."
    python "$INIT_DB_SCRIPT"
else
    echo "📁 Database already exists. Skipping initialization."
fi

