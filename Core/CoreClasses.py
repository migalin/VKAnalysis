# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

import vk_api
from PyQt5 import QtWidgets, QtGui
import re
from collections import defaultdict

VKAnalysisInfo = defaultdict(lambda: None)
VKAnalysisLoader = defaultdict(lambda: VKModuleDialog)


class VK(vk_api.VkApi):
    """
    Класс работы с VK API, наследник VkApi библиотеки vk_api.
    """
    def __init__(self, login, password, *args, **kwargs):
        """
        Коструктор
        Вызывет авторизацию пользователя автоматически.
        Имеет свой обработчик капчи.
        :param login: Логин пользователя
        :param password: Пароль пользователя
        :param args: параметры VkApi
        :param kwargs: параметры VkApi
        """
        super(VK, self).__init__(login, password, *args, **kwargs)
        self.auth()

    def captcha_handler(self, captcha_exception):
        """
        Обработчик капчи. Создает окно ввода капчи с картинки.
        :param captcha_exception: объект ошибки капчи
        :return: None
        """
        self.captcha_exception = captcha_exception
        self.captcha_dialog = QtWidgets.QDialog()
        self.captcha_dialog.setModal(True)
        image = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(self.captcha_exception.get_image())
        image.setPixmap(pixmap)
        button = QtWidgets.QPushButton("Отправить")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(image)
        self.edit = QtWidgets.QLineEdit()
        layout.addWidget(self.edit)
        layout.addWidget(button)
        button.clicked.connect(self.try_again)
        self.captcha_dialog.setLayout(layout)
        self.captcha_dialog.setWindowTitle("Введите капчу, чтобы продолжить")
        self.captcha_dialog.exec_()

    def try_again(self):
        """
        Выполняет повторный запрос с указанным в поле кода капчи.
        :return: разультат запроса
        """
        captcha_key = self.edit.text()
        self.captcha_dialog.close()
        return self.captcha_exception.try_again(key=captcha_key)


class VKErrorBox(QtWidgets.QMessageBox):
    """
    Окно вывода ошибки
    """

    T_GET_ID_ERR = ("Ошибка",
                    "Не удалось распознать посльзователя или группу. Попробуйте ввести ID.",
                    QtWidgets.QMessageBox.Warning)
    T_INET_ERR = ("Нет сети",
                  "Не удалось подключиться к сети Интернет",
                  QtWidgets.QMessageBox.Warning)

    def __init__(self, title, message, t):
        """
        Создает и открывает окно ошибки
        :param title: заголовок окна
        :param message: сообщение ошибки
        :param t: тип иконки MessageBox
        """
        super().__init__()
        self.setIcon(t)
        self.setWindowTitle(title)
        self.setText(message)
        self.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.exec_()


class VKModuleDialog(QtWidgets.QDialog):
    """
    Базовый класс для модулей приложения.
    Метод get_id_from_link(link) Преобразует ссылку ВК в id.
    """
    def __init__(self, vk, *args, **kwargs):
        """
        Конструктор окна модуля. Принимает объект VK как обязательный аргумент.
        :param vk:
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.vk = vk

    def get_id_from_link(self, link):
        """
        По ссылке ВК возвращает id пользователя или группы. Если получено число, то считает его за id.
        :param link: ссылка или id
        :return: id пользователя
        """
        id_regex = r"(^-?[\d]+)|(?:feed\?\w?=)?(?:wall|im\?sel=|id=*|photo|videos|albums|audios|topic)(-?[\d]+)|(?:club|public)([\d]*)|(?<=\.com/)([a-zA-Z\d._]*)"
        find_results = re.findall(id_regex, link)
        id = None
        if find_results:
            try:
                id_or_name = [el for el in find_results[0] if el]
                id = int(id_or_name[0])
            except ValueError:
                try:
                    resolved_name = self.vk.get_api().utils.resolveScreenName(screen_name=id_or_name[0])
                    id = resolved_name['object_id'] if resolved_name['type'] != 'applicaton' else None
                    if id is None:
                        raise TypeError
                    if resolved_name['type'] == 'group':
                        id = -id
                except KeyError:
                    raise TypeError
            return id
        else:
            raise TypeError
