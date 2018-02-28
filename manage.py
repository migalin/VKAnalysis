# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

import argparse
import os
import shutil
import re
import zipfile

# TODO: вместо этой кустарщины сделать скрипт установки и удаления в модулях


def module_list(name=None, mode='print'):
    """
    Показывает или возвращает установленные модули.
    Установленный - это тот, код инициализации обрамлен в # MODULE <name> ... # END <name>
    :param name: не используется
    :param mode: 'print' - печатает список, остальные значения = возврат списка
    :return: список названий модулей или None
    """
    modules = re.findall(r"# MODULE (.*)", open('Core/config.py', 'r').read())
    if mode != 'print':
        return modules
    print("Установлены следующие модули:")
    for i, module in enumerate(modules, 1):
        print(i, module)


def module_add(name=None):
    """
    Устанавливает новый модуль или заменяет старый.
    :param name: путь к файлу установки модуля.
    """
    if name is None or not os.path.isfile(name):
        print("Имя файла с модулем некорректно или пустое")
        return
    module_name = name.split('/')
    module_name = module_name[len(module_name)-1].split('.')[0]
    modules = module_list(mode='return')
    if module_name in modules:
        print("Модуль", module_name, "уже был установлен. Выполняется переустановка.")
        module_delete(name=module_name)
    print("Установка модуля", module_name)
    try:
        module = zipfile.ZipFile(name)
        install_script = module.open('install.py', 'r').read()
    except KeyError:
        print("Ошибка структуры модуля")
        return
    open('Core/config.py', 'a+').write("\n# MODULE "
                                       + module_name + "\n"
                                       + str(install_script, 'utf-8')
                                       + "\n# END " + module_name + "\n")
    for fn in module.namelist():
        module.extract(fn)
        os.rename(fn, fn.encode('cp437').decode('cp866'))
    os.remove('install.py')
    print("Модуль", module_name, "установлен")


def module_delete(name=None):
    """
    Удаляет установленный модуль
    :param name: имя модуля
    """
    modules = module_list(mode='return')
    if name not in modules or not os.path.exists(name):
        print("Модуль", name, "не найден")
        return
    print("Модуль", name, "удаляется")
    uninst = re.sub("# MODULE " + name + "(.|\n)*# END " + name, "", open('Core/config.py', 'r').read())
    open('Core/config.py', 'w').write(uninst)
    shutil.rmtree(name)


def clear_cache(name=None):
    """
    Очищает кэш авторизации.
    :param name: не используется
    """
    if not os.path.exists('auth.cached'):
        print("Кэш авторизации не найден")
        return
    os.remove('auth.cached')
    print("Кэш авторизации удален")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=True)
    actions = {
        'list': module_list,
        'add': module_add,
        'delete': module_delete,
        'clear': clear_cache,
    }
    parser.add_argument("action",
                        help="[add|delete|list] install, delete module or show installed. clear -- clear auth cache")
    parser.add_argument("name", action='store', nargs='?',
                        help="name of module/file")
    args = parser.parse_args()
    actions[args.action](args.name)
