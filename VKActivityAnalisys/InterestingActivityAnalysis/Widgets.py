import webbrowser
from PyQt5 import QtCore, QtWidgets, QtGui
from Core.CoreClasses import VKModuleDialog, VKErrorBox
from VKActivityAnalisys import ActivityAnalysis


class InterestingActivityAnalysisSettingsWidget(QtWidgets.QWidget):
    """
    Виджет настроек модуля анализов интересов
    """
    def __init__(self, parent=None):
        """
        Конструктор виджета
        :param parent: родительский объект
        """
        super(InterestingActivityAnalysisSettingsWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        """
        Инициализация интерфейса
        """
        self.settings_layout = QtWidgets.QGridLayout(self)
        self.uid_caption = QtWidgets.QLabel("ID Пользователя:")
        self.uid_caption.sizeHint()
        self.settings_layout.addWidget(self.uid_caption, 0, 0)

        self.uid_edit = QtWidgets.QLineEdit()
        self.uid_edit.setMinimumWidth(150)
        self.settings_layout.addWidget(self.uid_edit, 0, 1)

        self.period_caption = QtWidgets.QLabel("Загружать записей")
        self.settings_layout.addWidget(self.period_caption, 0, 2)

        self.limit_edit = QtWidgets.QLineEdit()
        self.limit_edit.setText("25")
        self.limit_edit.setMinimumWidth(70)
        self.settings_layout.addWidget(self.limit_edit, 0, 3)

        self.friends_checkbox = QtWidgets.QCheckBox("Проверять друзей")
        self.settings_layout.addWidget(self.friends_checkbox, 1, 0)

        self.groups_checkbox = QtWidgets.QCheckBox("Проверять сообщества")
        self.settings_layout.addWidget(self.groups_checkbox, 1, 2)

        self.progress = QtWidgets.QProgressBar()
        self.settings_layout.addWidget(self.progress, 2, 0, 1, 3)

        self.find_button = QtWidgets.QPushButton("Посмотреть")
        self.settings_layout.addWidget(self.find_button,2,3)

        self.setLayout(self.settings_layout)

    def setEnabled(self, mode):
        """
        Устанавливает доступность элементов
        :param mode: режим доступности
        :type mode: bool
        """
        self.uid_edit.setEnabled(mode)
        self.limit_edit.setEnabled(mode)
        self.friends_checkbox.setEnabled(mode)
        self.groups_checkbox.setEnabled(mode)


class InterestingActivityAnalysisWorker(QtCore.QThread):
    """
    Поток-получатель найденной информации
    """
    finished = QtCore.pyqtSignal()  # сигнал окончания проверки
    dictReady = QtCore.pyqtSignal(dict)  # сигнал получения определенного результата

    def __init__(self, vk_session, callback, uid, limit, parent=None, friends_need=False, groups_need=False):
        """
        Конструктор потока
        :param vk_session: сессия объекта VK
        :param callback: функция, выполняющаяся при получении очередного результата
        :param uid: id пользователя, которого проверяем
        :param limit: максимальное количество записей, которые загружаем
        :param parent: родительский объект
        :param friends_need: необходимость проверки друзей
        :param groups_need: необходимость проверки сообществ
        """
        QtCore.QThread.__init__(self, parent)
        self.interest_analysis = ActivityAnalysis.VKActivityAnalysis(vk_session)
        self.dictReady.connect(callback)
        self.uid = uid
        self.limit = limit
        self.friends_need = friends_need
        self.groups_need = groups_need
        self.close = False

    def run(self):
        """
        Действия потока
        """
        for element in self.interest_analysis.likes_friends_and_groups(uid=self.uid,
                                                                       limit=self.limit,
                                                                       friends_need=self.friends_need,
                                                                       groups_need=self.groups_need):
            if self.close:
                break
            self.dictReady.emit(element)
        self.finished.emit()


class InterestingActivityAnalysisItem(QtWidgets.QGroupBox):
    """
    Виджет записи, которую лайкнул пользователь
    """

    def __init__(self, title, image, link, text, parent=None):
        """
        Конструктор виджета
        :param title: Заголовок поста
        :param image: Изображение поста
        :param link: Ссылка на пост
        :param text: Текст поста (по умолчанию будет ...)
        :param parent: родительский объект
        """
        super().__init__(parent=parent)
        self.title = title
        self.image = image
        self.link = link
        self.text = text
        self.initUI()

    def initUI(self):
        """
        Инициализирует интерфейс
        """
        self.setStyleSheet("background-color: white")
        self.view = QtWidgets.QGridLayout()

        self.title_caption = QtWidgets.QLabel(self.title)
        self.title_caption.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
        self.view.addWidget(self.title_caption, 0, 0, 1, 5)

        self.link_caption = QtWidgets.QLabel(self.link)
        self.link_caption.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.StyleItalic))
        self.view.addWidget(self.link_caption, 1, 0, 1, 5)

        self.image_image = QtWidgets.QLabel()
        if isinstance(self.image, QtGui.QPixmap):
            self.image_image.setPixmap(self.image.scaledToWidth(130))
        self.view.addWidget(self.image_image, 2, 0)

        self.text_caption = QtWidgets.QLabel(self.text[:min(len(self.text), 300)] + '...')
        self.text_caption.setWordWrap(True)
        self.view.addWidget(self.text_caption, 2, 1, 1, 4)

        self.setLayout(self.view)

    def mousePressEvent(self, QMouseEvent):
        webbrowser.open(self.link)

    def enterEvent(self, *args, **kwargs):
        super().enterEvent(*args, **kwargs)
        self.setStyleSheet("background-color: #39CCCC")

    def leaveEvent(self, *args, **kwargs):
        super().leaveEvent(*args, **kwargs)
        self.setStyleSheet("background-color: white")


class InterestingActivityAnalysisWidget(VKModuleDialog):
    """
    Окно модуля анализа интересов
    """
    def __init__(self, vk, parent=None):
        """
        Конструктор окна
        :param vk: объект класса VK
        :param parent: родительский объект
        """
        super(InterestingActivityAnalysisWidget, self).__init__(vk=vk, parent=parent)
        self.vk = vk
        self.posts = []
        self.initUI()

    def initUI(self):
        """
        Инициализирует интерфейс
        """
        self.setWindowTitle("Анализ интересов пользователя")
        self.setWindowFlags(QtCore.Qt.Window)

        self.setMinimumHeight(600)
        self.setMinimumWidth(800)

        self.scroll_box = QtWidgets.QScrollArea()
        self.group_box = QtWidgets.QGroupBox()

        self.view = QtWidgets.QFormLayout()
        self.l = QtWidgets.QVBoxLayout()
        self.l.addWidget(self.scroll_box)

        self.caption = QtWidgets.QLabel("Изучение интересов пользователя")
        self.caption.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.caption.setMaximumHeight(50)
        self.view.addWidget(self.caption)

        self.settings = InterestingActivityAnalysisSettingsWidget()
        self.view.addWidget(self.settings)
        #self.view.addWidget(self.scroll_box)

        self.scroll_box.setWidget(self.group_box)
        self.group_box.setLayout(self.view)
        self.scroll_box.setWidgetResizable(True)
        self.setLayout(self.l)

        self.settings.find_button.clicked.connect(self.get_info)

    def get_info(self, pressed):
        """
        Запускает проверку
        :param pressed: рудимент Qt, не нужно
        """

        if self.settings.find_button.text() == 'Остановить':
            self.thread.close = True
            self.op_finished()
            return

        self.settings.setEnabled(False)
        self.settings.find_button.setText("Остановить")
        self.settings.progress.setValue(0)
        for element in self.group_box.children():
            if isinstance(element, InterestingActivityAnalysisItem):
                element.setParent(None)
                element.deleteLater()

        uid = 0
        limit = 0
        try:
            uid = self.get_id_from_link(self.settings.uid_edit.text())
            limit = int(self.settings.limit_edit.text())
        except (ValueError, TypeError):
            VKErrorBox(*VKErrorBox.T_GET_ID_ERR)
            return
        self.thread = InterestingActivityAnalysisWorker(vk_session=self.vk,
                                                        callback=self.add_item,
                                                        uid=uid,
                                                        limit=limit,
                                                        parent=None,
                                                        friends_need=self.settings.friends_checkbox.isChecked(),
                                                        groups_need=self.settings.groups_checkbox.isChecked())
        self.thread.finished.connect(self.op_finished)
        self.thread.start()

    def add_item(self, item):
        """
        Добавляет результат проверки на layout
        :param item: результат проверки
        """
        if 'album_id' in item:
            image = QtGui.QPixmap()
            image.loadFromData(self.vk.http.get(item['photo_130']).content)
            post = InterestingActivityAnalysisItem(title=item['name'],
                                                   image=image,
                                                   text=item['text'],
                                                   link='https://vk.com/photo' + str(item['owner_id']) + '_' + str(item['item_id']))
        elif 'post_type' in item:
            image = None
            text = ''
            if 'attachments' in item:
                if 'photo' in item['attachments'][0]:
                    if 'photo_130' in item['attachments'][0]['photo']:
                        image = QtGui.QPixmap()
                        image.loadFromData(self.vk.http.get(item['attachments'][0]['photo']['photo_130']).content)
            if 'text' in item:
                text = item['text']
            post = InterestingActivityAnalysisItem(title=item['name'],
                                                   image=image,
                                                   text=text,
                                                   link='https://vk.com/wall' + str(item['owner_id']) + '_' + str(item['item_id']))
        else:
            if 'count' in item:
                self.settings.progress.setMaximum(item['count'])
                self.settings.progress.setValue(item['current'])
            return

        self.posts += [post]
        self.view.addRow(post)

    def op_finished(self):
        """
        Выполняется по окончание проверки
        """
        self.settings.setEnabled(True)
        self.settings.find_button.setText("Посмотреть")
