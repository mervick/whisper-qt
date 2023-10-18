#!/usr/bin/env bash

all_ui=(app about progress)

pyrcc5 resources.qrc -o resources.py
for ui in ${all_ui[@]}; do
  pyuic5 -x $ui.ui -o ${ui}_ui.py
  sed -i -e 's/import\ resources_rc//g' ${ui}_ui.py
done

