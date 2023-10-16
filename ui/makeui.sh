#!/usr/bin/env bash

pyuic5 -x about.ui -o about.py
sed -i -e 's/import\ resources_rc/from\ \.\ import\ resources/g' about.py
pyrcc5 resources.qrc -o resources.py
