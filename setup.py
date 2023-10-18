additional_mods = ['appdirs', 'packaging.version']
additional_packages = ['scipy', 'numpy', 'appdirs', 'packaging']

setup(
    name="whisper-qt",
    version="1.0.0",
    description="Whisper QT transcriber",
    url="https://github.com/mervick/whisper-qt",
    author="Andrey Izman",
    author_email="izmanw@gmail.com",
    license="LGPLv3",
    classifiers=[
        "OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    packages=["whisper-qt"],
    include_package_data=True,
    install_requires=[
        "pyqt5==5.15.0", "pillow", "openai-whisper", "appdirs"
    ],
    options = {
        'build_exe': {
            'packages': additional_packages,
            'includes': additional_mods,
        }
    },
    entry_points={"console_scripts": ["realpython=app.app:main"]},
)

