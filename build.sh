#!/usr/bin/env bash

options=--paths ./ui/ --additional-hooks-dir ./ui/ --name whisper-qt

pyinstaller --onedir $options --contents-directory lib app.py
#pyinstaller --onefile $options app.py
