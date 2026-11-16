#!/usr/bin/env python3
"""Запуск Parser2GIS в один клик.

Скрипт сам делает всё необходимое:
  1. проверяет Python и tkinter;
  2. скачивает исходники проекта с GitHub (ветка с новым тёмным дизайном);
  3. создаёт отдельное виртуальное окружение и ставит зависимости;
  4. открывает окно программы.

Запуск:
    python run_parser_2gis.py            # открыть GUI
    python run_parser_2gis.py --update   # обновить исходники и зависимости
    python run_parser_2gis.py --cli -i "https://2gis.ru/..." -o out.csv -f csv

Зависимости не попадают в системный Python: всё лежит в ~/.parser-2gis-runner
(Windows: %USERPROFILE%\\.parser-2gis-runner). Удалите эту папку — и всё уберётся.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request

DEFAULT_BRANCH = 'arena/6de16037-parser-2gis'
ARCHIVE_URL = 'https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}'
OWNER = 'q984q'
REPO = 'parser-2gis'
MIN_PYTHON = (3, 9)
MARKER = '.deps-installed'


def log(message):
    print(f'[parser-2gis] {message}', flush=True)


def fail(message, code=1):
    print(f'\nОШИБКА: {message}', file=sys.stderr, flush=True)
    print('Если не получается — напишите текст ошибки, поможем.', file=sys.stderr, flush=True)
    sys.exit(code)


def work_dir():
    """Каталог, куда складываются исходники и виртуальное окружение."""
    custom = os.environ.get('PARSER_2GIS_DIR')
    if custom:
        return os.path.abspath(os.path.expanduser(custom))
    return os.path.join(os.path.expanduser('~'), '.parser-2gis-runner')


def venv_python(venv_dir):
    if os.name == 'nt':
        return os.path.join(venv_dir, 'Scripts', 'python.exe')
    return os.path.join(venv_dir, 'bin', 'python')


def check_python():
    if sys.version_info < MIN_PYTHON:
        fail(
            'нужен Python {}.{} или новее, а сейчас {}.{}.{}.\n'
            'Скачайте актуальный Python: https://www.python.org/downloads/'.format(
                MIN_PYTHON[0], MIN_PYTHON[1],
                sys.version_info[0], sys.version_info[1], sys.version_info[2],
            )
        )
    log(f'Python {platform.python_version()} — подходит.')


def check_tkinter():
    """tkinter нужен для окна. Без него программа работает только в CLI."""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        log('ВНИМАНИЕ: в этом Python нет tkinter — графическое окно не откроется.')
        if sys.platform.startswith('linux'):
            log('  Debian/Ubuntu: sudo apt install python3-tk')
            log('  Fedora:        sudo dnf install python3-tkinter')
        elif sys.platform == 'darwin':
            log('  Поставьте Python с https://www.python.org/downloads/ (там tkinter есть из коробки).')
        else:
            log('  Переустановите Python с python.org и включите компонент "tcl/tk and IDLE".')
        return False
    log('tkinter найден — окно программы доступно.')
    return True


def find_checkout(base):
    """Найти каталог с исходниками внутри рабочей папки (если он уже скачан)."""
    if not os.path.isdir(base):
        return None
    for name in sorted(os.listdir(base)):
        candidate = os.path.join(base, name)
        if os.path.isfile(os.path.join(candidate, 'setup.py')) and \
                os.path.isdir(os.path.join(candidate, 'parser_2gis')):
            return candidate
    return None


def download_sources(base, branch):
    """Скачать архив ветки с GitHub и распаковать его в `base`."""
    url = ARCHIVE_URL.format(owner=OWNER, repo=REPO, branch=branch)
    log(f'Скачиваю исходники: {url}')

    os.makedirs(base, exist_ok=True)
    tmp_path = os.path.join(base, 'sources.tar.gz')
    try:
        with urllib.request.urlopen(url, timeout=120) as response, open(tmp_path, 'wb') as out:
            shutil.copyfileobj(response, out)
    except urllib.error.HTTPError as e:
        fail(f'не удалось скачать исходники (HTTP {e.code}). Проверьте ветку "{branch}".')
    except urllib.error.URLError as e:
        fail(f'нет соединения с GitHub: {e.reason}')

    log('Распаковываю...')
    with tarfile.open(tmp_path, 'r:gz') as archive:
        archive.extractall(base)
    os.remove(tmp_path)

    checkout = find_checkout(base)
    if not checkout:
        fail('в архиве не нашлись файлы проекта.')
    log(f'Исходники готовы: {checkout}')
    return checkout


def ensure_venv(python_path):
    if os.path.isfile(python_path):
        return python_path
    log('Создаю виртуальное окружение (один раз, ~10 секунд)...')
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', os.path.dirname(os.path.dirname(python_path))])
    except subprocess.CalledProcessError:
        fail('не удалось создать виртуальное окружение (нужен модуль venv).')
    return python_path


def run_pip(python_path, args, cwd=None):
    command = [python_path, '-m', 'pip', 'install', '--disable-pip-version-check'] + args
    return subprocess.call(command, cwd=cwd)


def install_deps(python_path, checkout, force=False):
    marker = os.path.join(os.path.dirname(python_path), '..', MARKER)
    marker = os.path.normpath(marker)

    if os.path.isfile(marker) and not force:
        log('Зависимости уже установлены.')
        return

    log('Ставлю зависимости — это может занять пару минут...')
    subprocess.check_call([python_path, '-m', 'pip', 'install', '--disable-pip-version-check',
                           '--upgrade', 'pip'], stdout=subprocess.DEVNULL)

    rc = run_pip(python_path, ['-e', '.[gui]'], cwd=checkout)
    if rc != 0:
        log('Установка с extras "gui" не удалась, пробую базовые зависимости...')
        rc = run_pip(python_path, ['-e', '.'], cwd=checkout)
    if rc != 0:
        fail('не удалось установить зависимости (нет сети до PyPI или ошибка сборки).')

    # PySimpleGUI может не встать вместе с extras — проверяем и добиваем отдельно
    has_pysimplegui = subprocess.call(
        [python_path, '-c', 'import PySimpleGUI'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) == 0
    if not has_pysimplegui:
        log('Доставляю PySimpleGUI...')
        run_pip(python_path, ['PySimpleGUI>=4.60.5.1,<5'])

    with open(marker, 'w', encoding='utf-8') as f:
        f.write('ok\n')
    log('Зависимости установлены.')


def launch(python_path, checkout, extra_args, is_cli):
    if is_cli:
        command = [python_path, '-m', 'parser_2gis'] + extra_args
    else:
        log('Открываю окно Parser2GIS...')
        command = [python_path, '-m', 'parser_2gis']

    try:
        return subprocess.call(command, cwd=checkout)
    except KeyboardInterrupt:
        return 130


def main():
    parser = argparse.ArgumentParser(
        description='Запуск Parser2GIS: скачивает проект, ставит зависимости и открывает GUI.',
        add_help=True,
    )
    parser.add_argument('--branch', default=DEFAULT_BRANCH,
                        help=f'ветка GitHub (по умолчанию: {DEFAULT_BRANCH})')
    parser.add_argument('--dir', default=None,
                        help='куда скачать проект (по умолчанию ~/.parser-2gis-runner)')
    parser.add_argument('--update', action='store_true',
                        help='перекачать исходники и переустановить зависимости')
    parser.add_argument('--cli', action='store_true',
                        help='запустить консольный режим, аргументы после -- передаются парсеру')
    parser.add_argument('--dry-run', action='store_true',
                        help='всё подготовить, но не запускать программу')
    args, extra = parser.parse_known_args()

    if args.cli:
        extra = [a for a in extra if a != '--']

    if args.dir:
        os.environ['PARSER_2GIS_DIR'] = args.dir
    base = work_dir()

    log('Каталог установки: {}'.format(base))
    check_python()
    has_gui = check_tkinter()

    checkout = None if args.update else find_checkout(base)
    if checkout:
        log(f'Исходники уже на месте: {checkout}')
    else:
        if args.update and os.path.isdir(base):
            log('Удаляю старые исходники...')
            for name in os.listdir(base):
                path = os.path.join(base, name)
                if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'setup.py')):
                    shutil.rmtree(path, ignore_errors=True)
            marker = os.path.join(base, 'venv', MARKER)
            if os.path.isfile(marker):
                os.remove(marker)
        checkout = download_sources(base, args.branch)

    python_path = ensure_venv(venv_python(os.path.join(base, 'venv')))
    install_deps(python_path, checkout, force=args.update)

    if args.dry_run:
        log('Проверка завершена: всё готово к запуску.')
        return 0

    if not has_gui and not args.cli:
        log('GUI недоступен без tkinter — переключаюсь на консольный режим.')
        log('Пример: python run_parser_2gis.py --cli -i "URL" -o result.csv -f csv')
        return 1

    return launch(python_path, checkout, extra, args.cli)


if __name__ == '__main__':
    sys.exit(main())
