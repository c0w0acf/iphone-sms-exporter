📱 iPhone Message Exporter — Setup, Documentation & User Guide

Welcome! This application allows non-technical users to back up iPhone messages to a Windows PC and export them into clean, readable text (.txt) files.

📋 Prerequisites & Installation

Before running the application, make sure your computer has Python and the necessary dependencies installed.

1. Install Python (Windows)

If you do not have Python installed:

Download Python 3.x from the official website or open your Terminal/Command Prompt and run:

winget install Python.Python.3.12


CRITICAL: During manual installation, make sure to check the box that says "Add Python to PATH".

2. Verify Standard Libraries

This tool relies on built-in Python modules (tkinter, sqlite3, subprocess, threading, glob). No external pip packages are required.

To verify your Python environment is ready, open Command Prompt (cmd) and run:

python -c "import tkinter, sqlite3; print('Environment Ready!')"


3. Install Apple Devices (Microsoft Store)

To create local backups of your iPhone on Windows 10/11, install the official Apple Devices app from the Microsoft Store:

Option A (Automatic): The script will automatically detect if it is missing and offer to open the Microsoft Store page for you.

Option B (Manual Command): Run this command in Windows Terminal/Command Prompt to open the store page directly:

start ms-windows-store://pdp/?ProductId=9np83lwlpz9k


Option C (GUI): Search for Apple Devices in the Microsoft Store app and click Install.

🚀 Quick Start (4-Step Workflow)

Plug in Your iPhone

Connect your iPhone to your Windows PC using a USB/Lightning or USB-C cable.

Unlock your iPhone screen. If prompted with "Trust This Computer?", tap Trust and enter your passcode.

Launch the Exporter Application

Open Command Prompt, navigate to your folder, and run:

python sms_aio.py


The status bar at the top will illuminate blue, actively scanning for existing backups.

Create/Refresh Your Backup

Click Step 1: Open / Launch Apple Devices App inside the exporter window.

When Apple Devices opens, select your iPhone and click Back Up Now (ensure "Encrypt local backup" is UNCHECKED).

As soon as the backup finishes, the exporter app will automatically detect the fresh data, turn green, and load your contacts.

Export Your Messages

Select a specific person/number from the dropdown menu, OR check "Export every conversation on my phone".

(Optional) Enter a Start Date or End Date (YYYY-MM-DD) to narrow down the timeframe.

Click Export Messages to Text File. Your chat log will be saved as a clean .txt file!

🛠️ Troubleshooting & FAQ

1. The status bar says "Scanning..." and never turns green

Cause: A local backup has not been created yet, or Apple Devices is still backing up.

Fix:

Open Apple Devices and confirm the Back Up Now progress bar has finished.

Ensure the backup destination is set to "This Computer" (not iCloud).

Wait a few seconds—the background watcher inspects the folder every 3 seconds.

2. "The 'Apple Devices' app is not installed on this PC"

Cause: Missing Apple's official backup utility.

Fix: Click Yes on the pop-up prompt to launch the Microsoft Store and click Get/Install.

3. No contacts appear in the dropdown menu

Cause: The backup is encrypted or corrupted.

Fix:

In the Apple Devices app, uncheck "Encrypt local backup". (Encrypted backups lock the sms.db file with password encryption, preventing text extraction).

Run a new backup.

4. My exported text file is empty

Cause: Incorrect date formatting or no messages match the filter.

Fix:

Ensure date fields use the strict YYYY-MM-DD format (e.g., 2026-01-15).

Leave both date fields completely blank to export all history.