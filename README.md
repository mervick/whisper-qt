# Whisper QT - Whisper Crossplatform GUI Application

![01](https://github.com/mervick/whisper-qt/assets/2429298/96585787-5128-451f-b315-a5664e4c3971)

## Usage:

```sh
git clone https://github.com/mervick/whisper-qt
cd whisper-qt
python -m pip install -r requirements.txt
python app.py
```

#### Requirements:

- `python v3.10.12` (newer versions are not supported)
- `ffmpeg` (on windows `ffmpeg.exe` should be in the same dir)


### Create executable:

```sh
python -m pip install -r requirements.txt
pyinstaller app.spec
```

Created executable would be in the `dist` dir  
On windows you should put `ffmpeg.exe` in the root dir of the project

Tested on Ubuntu 22.04, Windows 10

## License

**Whisper QT** licensed under LGPLv3 license  
**OpenAI Whisper** licensed under MIT license  



