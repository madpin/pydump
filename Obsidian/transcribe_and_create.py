#!/usr/bin/env python3
import os
import time
import queue
import threading
import requests
import json
import datetime
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI

# Configuration
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OBSIDIAN_VAULT_DIR = os.getenv("OBSIDIAN_VAULT_DIR", "./Obsidian/dummy_vault")
MONITOR_DIR = os.getenv("MONITOR_DIR", "./Obsidian/audio_monitored")
AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac")

# Deepgram configuration
DEEPGRAM_BASE_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_PARAMS = {
    "model": "nova-2",
    "smart_format": "true",
    "punctuate": "true",
    "paragraphs": "true",
    "diarize": "true",
    "language": "en"
}

logging.basicConfig(level=logging.DEBUG)

def _is_audio_file(path):
    return path.lower().endswith(AUDIO_EXTS)

def _wait_for_stable(file_path, timeout=10, check_interval=0.1):
    """Wait until file size stabilizes"""
    start_time = time.time()
    last_size = -1
    stable_time = 0
    
    while time.time() - start_time < timeout:
        try:
            current_size = os.path.getsize(file_path)
            if current_size == last_size:
                stable_time += check_interval
                if stable_time >= 0.5:
                    return True
            else:
                last_size = current_size
                stable_time = 0
            time.sleep(check_interval)
        except FileNotFoundError:
            time.sleep(0.1)
    return False

def _get_content_type(file_path):
    """Get MIME type based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    return {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac'
    }.get(ext, 'audio/wav')

def _transcribe(file_path):
    """Transcribe audio using Deepgram API with parameterized URL"""
    try:
        content_type = _get_content_type(file_path)
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        
        # Build URL with parameters
        params = "&".join([f"{k}={v}" for k,v in DEEPGRAM_PARAMS.items()])
        url = f"{DEEPGRAM_BASE_URL}?{params}"
        
        with open(file_path, 'rb') as audio_file:
            response = requests.post(
                url,
                headers=headers,
                data=audio_file.read(),
                timeout=30
            )
        response.raise_for_status()
        
        # Parse nested response structure
        transcript = response.json().get('results', {}).get('channels', [{}])[0]
        transcript = transcript.get('alternatives', [{}])[0].get('transcript', '')
        
        if not transcript:
            logging.error(f"Empty transcript. Full response: {response.text[:200]}...")
            
        return transcript
        
    except Exception as e:
        logging.error(f"Transcription failed: {str(e)}")
        return f"Transcription error: {str(e)}"

def _get_calendar_context(file_path):
    """Generate date context header"""
    created_date = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
    return f"# {created_date.strftime('%Y-%m-%d %A')}\n\n"

def _save_note(content, audio_path):
    """Save transcript to Obsidian vault"""
    base_name = os.path.basename(audio_path).rsplit('.', 1)[0]
    date_str = datetime.date.today().strftime("%Y%m%d")
    note_path = os.path.join(OBSIDIAN_VAULT_DIR, f"{date_str}_{base_name}.md")
    
    os.makedirs(os.path.dirname(note_path), exist_ok=True)
    with open(note_path, 'w') as f:
        f.write(content)
    logging.info(f"Note saved: {note_path}")

def _generate_summary(transcript):
    """Generate summary using OpenAI"""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Generate concise summary and TL;DR. Respond with JSON: {summary: string, tldr: string}"
            }, {
                "role": "user",
                "content": transcript
            }],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("summary", ""), result.get("tldr", "")
    except Exception as e:
        logging.error(f"Summary generation failed: {str(e)}")
        return "", ""

def _process_file(file_path):
    """Main processing pipeline for audio files"""
    logging.info(f"Starting processing: {file_path}")
    
    if not _wait_for_stable(file_path):
        logging.warning(f"File not stable: {file_path}")
        return

    try:
        # Transcribe audio
        transcript = _transcribe(file_path)
        
        # Generate AI summaries
        summary, tldr = _generate_summary(transcript)
        
        # Build note content
        note_content = (
            f"## Transcription Summary\n\n{summary}\n\n"
            f"```tldr\n{tldr}\n```\n\n"
            f"{_get_calendar_context(file_path)}\n\n{transcript}"
        )
        
        # Save to Obsidian
        _save_note(note_content, file_path)
        
        logging.info(f"Successfully processed: {file_path}")
        
    except Exception as e:
        logging.error(f"Processing failed for {file_path}: {str(e)}")

def _play_audio(file_path):
    """Play audio file using system player"""
    try:
        subprocess.run(["afplay", file_path], check=True)
    except Exception as e:
        logging.error(f"Playback error: {str(e)}")

def _ask_yesno(prompt, file_path):
    """Interactive dialog with replay option"""
    script = f'''display dialog "{prompt}" buttons {{"↻ Replay", "✖ Cancel", "✓ Save"}} default button 3'''
    try:
        while True:
            output = subprocess.check_output(['osascript', '-e', script], text=True)
            if "✓ Save" in output:
                return True
            elif "✖ Cancel" in output:
                return False
            elif "↻ Replay" in output:
                _play_audio(file_path)
    except subprocess.CalledProcessError:
        return False

class AudioHandler(FileSystemEventHandler):
    def __init__(self, file_queue):
        self.file_queue = file_queue
        self.processed_files = set()

    def _handle_file(self, path):
        if _is_audio_file(path) and path not in self.processed_files:
            self.file_queue.put(path)
            self.processed_files.add(path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle_file(event.dest_path)

if __name__ == "__main__":
    observer = Observer()
    file_queue = queue.Queue()
    observer.schedule(AudioHandler(file_queue), MONITOR_DIR, recursive=False)
    observer.start()

    try:
        while True:
            try:
                file_path = file_queue.get_nowait()
                if _ask_yesno(f"Process {os.path.basename(file_path)}?", file_path):
                    threading.Thread(target=_process_file, args=(file_path,), daemon=True).start()
            except queue.Empty:
                time.sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()