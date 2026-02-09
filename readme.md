# Acompressio (unmantained)

A Telegram bot that compresses videos to a target file size using FFmpeg.

## Features

- 📹 Compress videos to 8/20/50/100 MB
- ⚡ Fast processing with FFmpeg
- 🚀 Background task queue with RQ
- 📦 Support for large files (up to 2GB) via Local Bot API

## Requirements

- Python 3.10+
- Redis
- FFmpeg & FFprobe
- Telegram Bot API Local Server (optional, for files > 20MB)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/telegram-video-compressor.git
cd telegram-video-compressor
```

### 2. Create virtual environment
 ```bash
 python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download FFmpeg
Download FFmpeg from https://github.com/BtbN/FFmpeg-Builds/releases
\
Extract ffmpeg.exe and ffprobe.exe to ffmpeg/ folder.

### 5. Setup environment variables

### 6. Start Redis
Windows:\
Download from https://github.com/microsoftarchive/redis/releases

Linux/Mac:
```bash
sudo systemctl start redis
# or
redis-server
```
Usage\
Option 1: Standard Bot API (files up to 20MB)\

Start the bot:
```bash
python main.py
```

Start RQ worker (in another terminal):
```bash
rq worker video -w rq.worker.SimpleWorker
```

Option 2: Local Bot API (files up to 2GB)\

Step 1: Setup Local Bot API Server

Get API credentials from https://my.telegram.org/apps

Download and run Telegram Bot API server:
```bash
telegram-bot-api --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local
```
Step 2: Start the bot (it will auto-connect to local server)
```bash
python main.py
```
Step 3: Start RQ worker
```bash
rq worker video -w rq.worker.SimpleWorker
```
## How It Works
1. User sends a video to the bot

2. Bot downloads video (or gets local path from Local Bot API)

3. User selects target file size (8/20/50/100 MB)

4. Bot queues compression task in RQ

5. Worker processes video with FFmpeg (two-pass encoding)

6. Bot sends compressed video back to user

## Troubleshooting
Error:
```bash
cannot pickle 'weakref.ReferenceType'
```
Make sure you're passing bot_token (string) to RQ tasks, not the bot object.

Error:
```bash
BUTTON_DATA_INVALID
```
Callback_data exceeds 64 bytes. The bot uses UUID to shorten IDs.


Error: RQ worker not processing jobs (Windows)\

Use SimpleWorker:
```bash
rq worker video -w rq.worker.SimpleWorker
```
## License
MIT License - feel free to use and modify!
## Contributing
I'm not mantaining this project anymore. Feel free to contribute.
## Author
![img.png](img.png)