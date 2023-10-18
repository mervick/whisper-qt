#!/usr/bin/env bash

#options=--paths ./ui/ --additional-hooks-dir ./ui/ --name whisper-qt
#pyinstaller --onedir $options --contents-directory lib app.py
#pyinstaller --onefile $options app.py

pyinstaller app.spec

rsync -a venv/lib/python3.10/site-packages/whisper/ dist/whisper-qt/lib/whisper/

rm dist/whisper-qt/lib/whisper/*.py
rm dist/whisper-qt/lib/whisper/*/*.py
