# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

import sys
import configparser
from PyQt5 import QtWidgets
from Core import VKAuthWidget, VKMenuWidget, VK, VKErrorBox
from vk_api.exceptions import AuthError, ApiError, ApiHttpError


class VKAnalysis:
    """
    Выполняет авторизацию и показывает главное меню.
    """

    def __init__(self):
        self.__auth = None
        self.__vk = None
        self.__app = None
        self.__config = configparser.ConfigParser()

    def run(self):
        """
        Запускает приложение.
        Показывает форму авторизации.
        :return:
        """
        self.__app = QtWidgets.QApplication(sys.argv)
        self.__auth = VKAuthWidget()
        self.__auth.auth_button.clicked.connect(self.__do_auth)
        self.__config.read('settings.ini')
        if 'Auth' in self.__config:
            self.__auth.login_edit.setText(self.__config['Auth']['User'])
            self.__auth.password_edit.setPlaceholderText("Пароль сохранен")
            self.__auth.password_edit.setFocus()
        self.__auth.exec_()

    def __do_auth(self, click=None):
        """
        Функция авторизации
        :param click: переменная event'а мыши
        :return: None
        """
        self.__auth.setEnabled(False)
        self.__auth.repaint()
        self.__config.read('settings.ini')
        if 'Auth' not in self.__config:
            self.__config.add_section('Auth')
        self.__config['Auth']['User'] = self.__auth.login_edit.text()
        try:
            self.__vk = VK(self.__auth.login_edit.text(),
                           self.__auth.password_edit.text(),
                           config_filename='auth.cached'
                           )
        except (AuthError, ApiError, ApiHttpError) as err:
            VKErrorBox("Ошибка", str(err), VKErrorBox.Warning)
            self.__vk = None
            self.__auth.setEnabled(True)
            return
        if self.__vk is not None:
            self.__auth.close()
            self.__config.write(open('settings.ini', 'w'))
            VKMenuWidget(self.__vk).exec_()


if __name__ == '__main__':
    VKAnalysis().run()
