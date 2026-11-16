#!/bin/bash
# Двойной клик в Finder/macOS открывает .command в Терминале
cd "$(dirname "$0")" || exit 1
python3 run_parser_2gis.py "$@"
status=$?
if [ $status -ne 0 ]; then
  echo
  read -n 1 -s -r -p "Нажмите любую клавишу, чтобы закрыть..."
fi
exit $status
