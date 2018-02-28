# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

import os

from PyQt5 import QtWidgets, QtGui, QtCore
from .config import *
from .MenuItemWidget import VKMenuItemWidget


class VKMenuWidget(QtWidgets.QDialog):
    """
    Виджет меню приложения.
    """

    def __init__(self, vk, parent=None):
        """
        Конструктор виджета
        :param vk: объект класса VK
        :param parent: родительский объект
        """
        super(VKMenuWidget, self).__init__(parent=parent)
        self.vk = vk
        self.initUI()

    def run_dialog(self, name):
        """
        Запускает модуль на выполнение
        :param name: имя модуля
        """
        VKAnalysisLoader[name](self.vk).exec_()

    def initUI(self):
        """
        Инициализирует интерфейс
        """
        self.setWindowTitle("VKAnalysis " + str(VKAnalysisInfo['version']))
        self.setStyleSheet("background-color: white;")

        self.setFixedSize(1100, 800)
        self.layout = QtWidgets.QVBoxLayout()

        self.header_layout = QtWidgets.QGridLayout()

        self.logo = QtWidgets.QLabel()
        self.dirname = os.path.dirname(__file__)
        pic = QtGui.QPixmap()
        logo_path = os.path.join(self.dirname, 'images/logo_small.PNG')
        if os.path.isfile(logo_path):
            pic.loadFromData(open(logo_path, 'rb').read())
            pic = pic.scaledToHeight(64)
            self.logo.setPixmap(pic)
        icon_path = os.path.join(self.dirname, 'images/icon.ico')
        if os.path.isfile(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        self.header_layout.addWidget(self.logo, 0, 0)

        self.user_photo = QtWidgets.QLabel()
        self.user_photo_caption = QtWidgets.QLabel()
        api = self.vk.get_api()
        info = api.users.get(fields='photo_100')[0]
        photo_url = info['photo_100']
        pic.loadFromData(self.vk.http.get(photo_url).content)
        self.user_photo.setPixmap(pic)
        self.user_photo_caption.setText("<html>Вы вошли как <b>" + info['first_name'] + "</b></html>")
        self.user_photo_caption.setFont(QtGui.QFont("Times", 12))
        margin = QtWidgets.QLabel()
        margin.setFixedWidth(970)
        self.header_layout.addWidget(margin, 0,1)
        self.header_layout.addWidget(self.user_photo_caption, 0 ,2, QtCore.Qt.AlignRight)
        self.header_layout.addWidget(self.user_photo, 0, 3, QtCore.Qt.AlignLeft)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)

        #self.scroll.setFixedHeight(500)
        self.mygroupbox = QtWidgets.QGroupBox()
        self.scroll.setStyleSheet("border:0; background-color: white;")
        self.scroll.setWidget(self.mygroupbox)
        menu = VKAnalysisLoader.keys()
        self.menu = []

        self.menu_layout = QtWidgets.QGridLayout()
        for i, item in enumerate(menu):
            mi = VKMenuItemWidget(item)
            self.menu.append(mi)
            mi.setParent(self.mygroupbox)
            self.menu_layout.addWidget(mi,i//2, i%2)
            mi.clicked.connect(self.run_dialog)

        self.mygroupbox.setLayout(self.menu_layout)

        self.mygroupbox.resize(self.mygroupbox.width(), len(self.menu)*150+150)
        self.scroll.setWidget(self.mygroupbox)

        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.scroll)

        self.setLayout(self.layout)

        self.scroll.update()
