#!/usr/bin/env python3

"""
To use:
1. install/set-up the google cloud api and dependencies listed on https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/texttospeech/cloud-client
2. install pandoc and pypandoc, also tqdm
3. create and download a service_account.json ("Service account key") from https://console.cloud.google.com/apis/credentials
4. run GOOGLE_APPLICATION_CREDENTIALS=service_account.json python make_audiobook.py book_name.epub
"""

import os
import srt
import time
import itertools
import subprocess
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path

from google.cloud import texttospeech
from tqdm import tqdm

# see https://cloud.google.com/text-to-speech/quotas

MAX_REQUESTS_PER_MINUTE = 200
MAX_CHARS_PER_MINUTE = 135000
MAX_SEN_COUNT_PER_CHUNK = 2
START_FROM_CHUNK = 0
CREATE_SRT = True
BOOK_FILE = Path('small_fixed.txt')

AUDIO_CHUNKS_DIR = Path('Audio_chunks')
TEXT_CHUNKS_DIR = Path('Text_chunks')

MP3_FILE_NAME = BOOK_FILE.with_suffix('.mp3')
SRT_FILE_NAME = BOOK_FILE.with_suffix('.srt')

def get_master_file_length_in_secs():
    cmd = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1'.split()
    cmd.append(MP3_FILE_NAME.absolute())
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = proc.communicate()[0].decode()

    length = 0
    if out:
        length = float(out)
    return length

def create_mp4():
    print('Creating video file...')
    cmd = 'ffmpeg -i -i cover.jpg -f mp4'.split()
    cmd.append(MP3_FILE_NAME.with_suffix('.mp4').absolute())
    cmd.insert(2, MP3_FILE_NAME.absolute())
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    print('Video file created!')

def get_text_chunk_for_processing(text):
    joined_sen = ''
    for sen in text.split('.'):
        sen +=  '.'
        if joined_sen.count('.') < MAX_SEN_COUNT_PER_CHUNK:
            joined_sen += sen
        else:
            yield joined_sen.strip()
            joined_sen = sen
    if joined_sen.strip():
        yield joined_sen.strip()

def write_text_and_audio_chunk(i, audio_chunk, text_chunk):
    with (AUDIO_CHUNKS_DIR / str(i)).open(mode='wb') as f:
        f.write(audio_chunk)
    with (TEXT_CHUNKS_DIR / str(i)).open(mode='w') as f:
        f.write(text_chunk)
    

def get_chunks_count(text):
    # Safest but extensive. Contributions welcomed!
    c = 0
    for chunk in get_text_chunk_for_processing(text):
        c += 1
    return c

    sen_count = text.count('.')
    chunks_count = sen_count // MAX_SEN_COUNT_PER_CHUNK
    if (sen_count % MAX_SEN_COUNT_PER_CHUNK):
        chunks_count += 1
    return chunks_count

class Narrator:
    def __init__(self, voice_name="en-US-News-K"):
        # "en-US-Wavenet-F" is also good. But costly too.
        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name=voice_name
        )
        
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
            # pitch=-3,
            # speaking_rate=0.8
        )
        
        # Rate limit stuff
        self._minute = -1
        self._requests_this_minute = 0
        self._chars_this_minute = 0

    def print_voice_names(self, lang="en"):
        print("Available voices for language {}:".format(lang))
        for voice in self.client.list_voices().voices:
            if voice.name.startswith(lang):
                print(voice.name)

    def _rate_limit(self):
        if (
            self._requests_this_minute > MAX_REQUESTS_PER_MINUTE
            or self._chars_this_minute > MAX_CHARS_PER_MINUTE
        ):
            while dt.now().minute == self._minute:
                time.sleep(5)
        if dt.now().minute != self._minute:
            self._minute = dt.now().minute
            self._requests_this_minute = 0
            self._chars_this_minute = 0

    def _text_chunk_to_audio_chunk(self, text_chunk):
        self._rate_limit()
        input_text = texttospeech.SynthesisInput(text=text_chunk)
        response = self.client.synthesize_speech(
            input=input_text, voice=self.voice, audio_config=self.audio_config
        )
        self._requests_this_minute += 1
        self._chars_this_minute += len(text_chunk)
        return response.audio_content

    def text_file_to_mp3_file(self):
        with open(BOOK_FILE) as f:
            text = f.read().strip()
        # lines = text.splitlines()
        text_chunks = get_text_chunk_for_processing(text)
        subtitle_parts = []

        with MP3_FILE_NAME.open("wb") as out:
            global START_FROM_CHUNK
            if START_FROM_CHUNK:
                START_FROM_CHUNK -= 1
            for i, text_chunk in enumerate(itertools.islice(tqdm(text_chunks, total=get_chunks_count(text), desc='Progress'), START_FROM_CHUNK, None), START_FROM_CHUNK):
                # skip empty lines
                if text_chunk:


                    audio_chunk = self._text_chunk_to_audio_chunk(text_chunk)
                    write_text_and_audio_chunk(i, audio_chunk, text_chunk)
                    if CREATE_SRT: start_time = get_master_file_length_in_secs()
                    out.write(audio_chunk)
                    if CREATE_SRT: end_time = get_master_file_length_in_secs()
                    if CREATE_SRT: subtitle_parts.append(srt.Subtitle(0, timedelta(seconds=start_time), timedelta(seconds=end_time-0.1), text_chunk, proprietary=''))
        
        with SRT_FILE_NAME.open('w') as f:
            f.write(srt.compose(subtitle_parts))



def main():
    assert BOOK_FILE.exists(), 'File not found!'
    input('Please ensure your chunks directories are empty or deleted. Press enter to continue: ')
    print()
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'STAGING_FOLDER/AllProjects-ServiceAccountKey.json'
    AUDIO_CHUNKS_DIR.mkdir(exist_ok=True)
    TEXT_CHUNKS_DIR.mkdir(exist_ok=True)

    narrator = Narrator()
    narrator.text_file_to_mp3_file()

    print("Generated:", MP3_FILE_NAME)
    if input('Create video file too? (y/n): ') == 'y' : create_mp4()

if __name__ == "__main__":
    main()