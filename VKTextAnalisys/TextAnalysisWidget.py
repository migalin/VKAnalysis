# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

from PyQt5 import QtCore, QtWidgets, QtGui

from Core.CoreClasses import VKErrorBox, VKModuleDialog
from .TextAnalysisAdditionalWidgets import PostTextWidget, TextAnalysisWorker, VKTextAnalysisSettingsWidget


class VKTextAnalysisWidget(VKModuleDialog):
    """
    Виджет проверки текстовой информации на страницах пользователей и сообществ
    """

    def __init__(self, vk, parent=None):
        """
        Конструктор виджета
        :param vk: объект VkApi
        :param parent: одительский объект
        """
        super(VKTextAnalysisWidget, self).__init__(vk=vk, parent=parent)
        self.initUI()

    def initUI(self):
        """
        Инициализация графического интрфейса
        :return: None
        """
        self.setWindowTitle("Анализатор текста постов")
        self.setWindowFlags(QtCore.Qt.Window)

        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        self.view = QtWidgets.QVBoxLayout()
        self.scroll_view = QtWidgets.QFormLayout()
        self.group_box = QtWidgets.QGroupBox()
        self.group_box.setLayout(self.scroll_view)
        self.scroll_area = QtWidgets.QScrollArea()
        self.view.addWidget(self.scroll_area)

        self.scroll_area.setWidget(self.group_box)
        self.scroll_area.setWidgetResizable(True)

        self.setLayout(self.view)

        self.caption = QtWidgets.QLabel('Анализатор текста постов')

        self.caption.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.caption.setMaximumHeight(50)
        self.scroll_view.addWidget(self.caption)

        self.settings = VKTextAnalysisSettingsWidget()
        self.scroll_view.addWidget(self.settings)

        self.settings.find_button.clicked.connect(self.start)

    def delete_posts(self):
        """
        Удаление всех виджетов постов
        :return: None
        """
        for element in self.group_box.children():
            if isinstance(element, PostTextWidget):
                element.setParent(None)
                element.deleteLater()

    def start(self):
        """
        Запуск проверки страницы пользователя или сообщества
        :return: None
        """
        self.settings.progress.setValue(0)  # обнуляем прогресс бар

        if self.settings.find_button.text() == 'Остановить':  # выбираем действие на кнопке
            self.thread.close = True
            return

        dicts = []
        limit = 2500

        try:
            uid = self.get_id_from_link(self.settings.uid_edit.text())
            limit = int(self.settings.limit_edit.text())
            for checkbox in self.settings.settings_checkboxes:
                if checkbox.isChecked():
                    dicts.append(checkbox.text())
            self.settings.setEnabled(False)
            self.settings.find_button.setText("Остановить")
        except (TypeError, ValueError):
            VKErrorBox(*VKErrorBox.T_GET_ID_ERR)
            return

        self.delete_posts()
        self.thread = TextAnalysisWorker(uid=uid,
                                         vk_session=self.vk,
                                         callback=self.add_post,
                                         dicts_need=dicts,
                                         limit=limit)
        self.thread.finished.connect(self.op_finished)
        self.thread.start()

    def op_finished(self):
        """
        Действие после окончания проверки.
        Меняет текст кнопки на другое действие и устанавливает доступными все элементы
        :return: None
        """
        self.settings.find_button.setText("Проверить")
        self.settings.setEnabled(True)

    def add_post(self, data):
        """
        Добавление поста на экран
        :param data: Пост в формате, возвращаемом VKTextAnalysis
        :return: None
        """
        self.settings.progress.setMaximum(data['count'])
        self.settings.progress.setValue(data['current'])
        if data['info'] or self.settings.all_posts.isChecked():
            post = PostTextWidget(data)
            self.scroll_view.addRow(post)
