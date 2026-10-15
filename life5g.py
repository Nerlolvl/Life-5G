#!/usr/bin/env python3
"""Life:) BY 5G: ставит первый пакет из списка, который подтвердит iOS этой версии.

Работает одинаково с физической SIM и с eSIM: привязка идёт по IMSI, слот и тип
SIM не важны. По умолчанию обрабатываются все SIM операторов России и Беларуси
(--sims all); зарубежная SIM без своей строки в bundle.yaml не трогается.

Если пакета нет в этой версии iOS, carrier.py сам откатывает настройки
(код выхода 3 и строка «Прежние настройки возвращены») — тогда берётся следующий
пакет из списка. Иное «не подтверждено» останавливает перебор: ссылка могла уже
заработать, и заменять её вслепую нельзя.
"""
from __future__ import annotations
import os
import signal
import subprocess
import sys

import launch

# Порядок попыток: первый подтверждённый iOS пакет остаётся. Правьте под себя,
# имена — как папки в /System/Library/Carrier Bundles/iPhone на телефоне.
# Свойства пакетов: https://ios-bundles.github.io (см. также README.md).
# Turkcell_lifecell_ua — «Life» (lifecell ua): 5G + EVS + VoLTE-переключатель.
# Vodafone_hu — самый обкатанный пакет сообщества (Авто 5G, XCAP, VoWiFi).
BUNDLES = ('Turkcell_lifecell_ua', 'Vodafone_hu', 'O2_Germany')

ROLLED_BACK = 'Прежние настройки возвращены'
UNCONFIRMED_KEEP = 'Каталог записан, но журнал не подтвердил выбор'


def run_capture(python, args):
    # Живой вывод в консоль + копия в память, чтобы различать исходы по тексту.
    # SIGINT проглатывается в родителе: carrier.py должен успеть вернуть Books.
    previous = signal.signal(signal.SIGINT, lambda *_: None)
    printed = []
    try:
        proc = subprocess.Popen([str(python), '-u', str(launch.ROOT / 'carrier.py'), *args],
                                cwd=launch.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace')
        for line in proc.stdout:
            print(line, end='')
            printed.append(line)
        return proc.wait(), ''.join(printed)
    finally:
        signal.signal(signal.SIGINT, previous)


def parse_args(argv):
    if '-h' in argv or '--help' in argv:
        # Просто показать справку carrier.py, не запуская установку.
        return None, ['--help']
    sims, rest = 'all', []
    while argv:
        item = argv.pop(0)
        if item == '--sims':
            require_sims_value(argv)
            sims = argv.pop(0)
        elif item in ('--bundle', '--bundles'):
            raise SystemExit('Флаг ' + item + ' не используется: порядок пакетов задаёт список '
                             'BUNDLES в начале life5g.py.')
        else:
            rest.append(item)
    if sims not in ('1', '2', 'all'):
        raise SystemExit('--sims: только 1, 2 или all (получено: ' + sims + ').')
    return sims, rest


def require_sims_value(argv):
    if not argv or argv[0].startswith('--'):
        raise SystemExit('Флаг --sims требует значения: 1, 2 или all.')


def show_status(python):
    print('\n  Текущее состояние:', flush=True)
    subprocess.run([str(python), '-u', str(launch.ROOT / 'carrier.py'), '--status'], cwd=launch.ROOT)


def main():
    os.environ.setdefault('PYTHONUTF8', '1')
    sims, extra = parse_args(sys.argv[1:])
    launch.check_writable()
    python = launch.python_environment()
    if sims is None:
        return subprocess.run([str(python), '-u', str(launch.ROOT / 'carrier.py'), *extra],
                              cwd=launch.ROOT).returncode
    print('\n  life:) 5G · пакеты в порядке попыток: ' + ', '.join(BUNDLES)
          + '  ·  SIM: ' + sims, flush=True)
    for number, bundle in enumerate(BUNDLES, 1):
        print(f'\n=== Попытка {number}/{len(BUNDLES)}: {bundle} ===', flush=True)
        code, out = run_capture(python, ['--bundle', bundle, '--sims', sims, *extra])
        if code == 0:
            print('\n  Готово: iOS этой версии выбрала ' + bundle + '. Перезагрузите iPhone и включите 5G '
                  'по README.md (Голос и данные → 5G вкл).', flush=True)
            return 0
        if code == launch.UNCONFIRMED and ROLLED_BACK in out:
            print('\n  Пакета ' + bundle + ' нет в этой версии iOS — настройки откатены, пробую следующий.', flush=True)
            continue
        if code == launch.UNCONFIRMED:
            print('\n  iOS не подтвердила ' + bundle + ' по журналу, но и не отвергла: ссылка осталась записана. '
                  'Перебор остановлен, чтобы не затереть возможно рабочий пакет.', flush=True)
            show_status(python)
            return launch.UNCONFIRMED
        print('\n  Ошибка (код ' + str(code) + '). Попытки прекращены; телефон не изменён или откатен.', flush=True)
        return code
    print('\n  Ни один пакет не подтверждён iOS этой версии. Проверьте версию iPhone/iOS (README.md) '
          'и журнал последней операции в папке runs.', flush=True)
    return launch.UNCONFIRMED


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
