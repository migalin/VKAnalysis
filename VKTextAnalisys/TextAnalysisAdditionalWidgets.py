# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import webbrowser
from . import TextAnalysisCore
import os


class VKTextAnalysisSettingsWidget(QtWidgets.QWidget):
    """
    Виджет настройки модуля
    """
    def __init__(self, parent=None):
        super(VKTextAnalysisSettingsWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        """
        Инициализация графического интерфейса
        :return: None
        """
        self.settings_layout = QtWidgets.QGridLayout(self)
        self.uid_caption = QtWidgets.QLabel("ID/ссылка:")
        self.uid_caption.sizeHint()
        self.settings_layout.addWidget(self.uid_caption, 0, 0)

        self.uid_edit = QtWidgets.QLineEdit()
        self.uid_edit.setMinimumWidth(150)
        self.settings_layout.addWidget(self.uid_edit, 0, 1)

        self.period_caption = QtWidgets.QLabel("Загружать записей")
        self.settings_layout.addWidget(self.period_caption, 0, 2)

        self.limit_edit = QtWidgets.QLineEdit()
        self.limit_edit.setText("2500")
        self.limit_edit.setMinimumWidth(70)
        self.settings_layout.addWidget(self.limit_edit, 0, 3)

        self.settings_checkboxes = []

        for dictionary in os.listdir(os.path.join(os.path.dirname(__file__), 'dicts')):
            obj = QtWidgets.QCheckBox(dictionary)
            obj.setChecked(True)
            self.settings_checkboxes.append(obj)
            self.settings_layout.addWidget(obj)

        self.all_posts = QtWidgets.QCheckBox("Показывать все")
        self.settings_checkboxes.append(self.all_posts)
        self.settings_layout.addWidget(self.all_posts)

        self.progress = QtWidgets.QProgressBar()
        self.settings_layout.addWidget(self.progress, 3,0,1,3)

        self.find_button = QtWidgets.QPushButton("Проверить")
        self.settings_layout.addWidget(self.find_button,3,3)

        self.setLayout(self.settings_layout)

    def setEnabled(self, mode):
        """
        Устанавливает доступность элементов интерфейса во время работы
        :param mode: доступность
        :type mode: bool
        :return: None
        """
        self.uid_edit.setEnabled(mode)
        self.limit_edit.setEnabled(mode)
        for checkbox in self.settings_checkboxes:
            checkbox.setEnabled(mode)


class PostTextWidgetInfo(QtWidgets.QDialog):
    """
    Окно подробного отчета по посту
    """
    def __init__(self, parent=None, bolds=[]):
        super().__init__(parent=parent)
        self.setModal(True)
        self.setWindowTitle("Подробный отчет")
        self.t = QtWidgets.QTextEdit(self)
        text = "Подробный отчет по посту: \n"
        self.t.setText(text)
        for bold in bolds:
            text += bold[4] + " в слове \"" + bold[3] + "\"\n"
        self.t.setText(text)
        self.t.setFixedHeight(400)
        self.t.setFixedWidth(600)
        self.setFixedWidth(600)
        self.setFixedHeight(400)


class QLinkLabel(QtWidgets.QLabel):
    """
    Label со ссылкой, открывается в браузере
    """
    def __init__(self, link='', parent=None):
        """
        Конструктор элемента
        :param link: ссылка
        :param parent: родительский объект
        """
        self.link = link
        super().__init__('<html><a href="#">' +self.link + '</a></html>')

    def mousePressEvent(self, QMouseEvent):
        """
        Событие по клику. Открывает ссылку в браузере.
        :param QMouseEvent: событие клика
        :return: None
        """
        super().mousePressEvent(QMouseEvent)
        webbrowser.open(self.link)


class QPostLabel(QtWidgets.QLabel):
    """
    Элемент текста поста.
    Имеет изменение цвета при наведении, а также создает окно подробного отчета при клике.
    """
    def __init__(self, text, bolds):
        """
        Конструктор
        :param text: текст поста (можно в HTML)
        :param bolds: пометки VKTextAnalysis для данного поста
        """
        super().__init__(text)
        self.bolds = bolds
        self.setToolTip('Нажмите для подробного отчета')

    def enterEvent(self, *args, **kwargs):
        """
        Событие наведения мыши. Меняет цвет фона.
        """
        super().enterEvent(*args, **kwargs)
        self.setStyleSheet("background-color: #40e8e8")
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, *args, **kwargs):
        """
        Событие покидания мышью оюъекта. Меняет цвет фона.
        """
        super().leaveEvent(*args, **kwargs)
        self.setStyleSheet("background-color: #39CCCC")
        self.setCursor(QtCore.Qt.ArrowCursor)

    def mousePressEvent(self, QMouseEvent):
        """
        Событие клика по тексту. Создает окно подробного отчета
        :param QMouseEvent:
        :return:
        """
        super().mousePressEvent(QMouseEvent)
        PostTextWidgetInfo(parent=None, bolds=self.bolds).exec_()


class PostTextWidget(QtWidgets.QGroupBox):
    """
    Виджет поста
    """

    def __init__(self, data, parent=None):
        """
        Конструктор
        :param data: данные, возвращаемые VKTextAnalysis
        :param parent: родительский объект
        """
        super().__init__(parent)
        self.link = data['link']
        self.bolds = data['info']
        self.initUI(data)

    def initUI(self, data):
        """
        Инициалиация графического интерфейса
        :param data: данные, возвращаемые VKTextAnalysis
        :return:
        """
        # TODO: убрать параметр
        self.setStyleSheet('background-color: white;')

        self.view = QtWidgets.QVBoxLayout()
        self.setLayout(self.view)

        fio = data['user']['first_name'] + ' ' + data['user']['last_name']
        self.caption = QtWidgets.QLabel('<html><b>' + fio + "</b></html>")
        self.view.addWidget(self.caption)

        self.link_caption = QLinkLabel(self.link)
        self.view.addWidget(self.link_caption)

        self.text = QPostLabel(data['html'], self.bolds)
        self.text.setWordWrap(True)
        self.view.addWidget(self.text)

    def enterEvent(self, *args, **kwargs):
        """
        Событие наведения мыши. Меняет цвет фона.
        """
        super().enterEvent(*args, **kwargs)
        self.setStyleSheet("background-color: #39CCCC")
        self.text.setStyleSheet("background-color: #39CCCC")

    def leaveEvent(self, *args, **kwargs):
        """
        Событие покидания мыши. Меняет цвет фона.
        """
        super().leaveEvent(*args, **kwargs)
        self.setStyleSheet("background-color: white")
        self.text.setStyleSheet("background-color: white")


class TextAnalysisWorker(QtCore.QThread):
    """
    Поток выполнения проверки текста
    """

    finished = QtCore.pyqtSignal()
    dictReady = QtCore.pyqtSignal(dict)

    def __init__(self, vk_session, uid, callback, dicts_need, limit=2500, parent=None):
        """
        Конструктор потока
        :param vk_session: VkApi объект
        :param uid: id пользователя или группы
        :param callback: функция, которая исполнится по завершении
        :param dicts_need: какие словари нужны
        :param limit: максимальное количество загружаемых записей
        :param parent: родительский объект
        """
        QtCore.QThread.__init__(self, parent)
        self.uid = uid
        self.limit = limit
        self.text_analysis = TextAnalysisCore.VKTextAnalysis(vk_session, dicts_need=dicts_need)
        self.dictReady.connect(callback)
        self.close = False

    def run(self):
        """
        Работа потока.
        Генератор результатов проверок.
        """
        for element in self.text_analysis.check_wall_iterable(self.uid, limit=self.limit):
            if self.close:
                break
            self.dictReady.emit(element)
        self.finished.emit()

