# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

from PyQt5 import QtWidgets, QtGui, QtCore
import os


class VKAuthWidget(QtWidgets.QDialog):
    """
    Виджет авторизации пользователя Вконтакте
    """
    def __init__(self, parent=None):
        """
        Конструктор виджета авторизации
        :param parent: родительский объект
        """
        super(VKAuthWidget, self).__init__(parent)
        self.vk = None
        self.initUI()

    def initUI(self):
        """
        Создание графического интерфейса (Qt Style)
        :return: None
        """
        self.setWindowTitle("VK Analisys: Авторизация")
        self.dirname = os.path.dirname(__file__)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        icon_path = os.path.join(self.dirname, 'images/icon.ico')
        if os.path.isfile(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self.setFixedSize(600, 300)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.login_layout = QtWidgets.QHBoxLayout()
        self.login_caption = QtWidgets.QLabel("Логин")
        self.login_edit = QtWidgets.QLineEdit()
        self.login_layout.addWidget(self.login_caption)
        self.login_layout.addWidget(self.login_edit)

        self.password_layout = QtWidgets.QHBoxLayout()
        self.password_caption = QtWidgets.QLabel("Пароль")
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_layout.addWidget(self.password_caption)
        self.password_layout.addWidget(self.password_edit)

        self.header = QtWidgets.QLabel()
        self.dirname = os.path.dirname(__file__)
        pic = QtGui.QPixmap()
        logo_path = os.path.join(self.dirname, 'images/logo.PNG')
        if os.path.isfile(logo_path):
            pic.loadFromData(open(logo_path, 'rb').read())
            pic = pic.scaledToHeight(100)
            self.header.setPixmap(pic)
        self.header.setMaximumHeight(100)

        self.auth_button = QtWidgets.QPushButton("Войти")

        self.layout.addWidget(self.header)
        self.layout.addLayout(self.login_layout)
        self.layout.addLayout(self.password_layout)
        self.layout.addWidget(self.auth_button)

    def setEnabled(self, enabled):
        """
        Делает доступными/недоступными элементы окна на время авторизации.
        :param enabled: доступность
        :type enabled: bool
        :return: None
        """
        self.auth_button.setEnabled(enabled)
        self.login_edit.setEnabled(enabled)
        self.password_edit.setEnabled(enabled)
