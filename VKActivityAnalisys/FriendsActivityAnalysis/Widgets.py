from PyQt5 import QtCore, QtWidgets, QtGui
from VKActivityAnalisys import ActivityAnalysis
from Core.CoreClasses import VKErrorBox, VKModuleDialog


class FriendsActivityAnalysisSettingsWidget(QtWidgets.QWidget):
    """
    Виджет настроек модуля Анализа круга общения
    """
    def __init__(self, parent=None):
        """
        Конструктор виджета
        :param parent: родительский объект
        """
        super(FriendsActivityAnalysisSettingsWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        """
        Инициализирует интерфейс
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

        self.likes_friends_checkbox = QtWidgets.QCheckBox("Лайки друзьям")
        self.settings_layout.addWidget(self.likes_friends_checkbox, 1, 0)

        self.likes_self_checkbox = QtWidgets.QCheckBox("Лайки друзей у польз.")
        self.settings_layout.addWidget(self.likes_self_checkbox, 1, 1)

        self.common_friends_checkbox = QtWidgets.QCheckBox("Общие друзья")
        self.settings_layout.addWidget(self.common_friends_checkbox, 1, 2)

        self.common_city_checkbox = QtWidgets.QCheckBox("Общий город")
        self.settings_layout.addWidget(self.common_city_checkbox, 1, 3)

        self.common_age_checkbox = QtWidgets.QCheckBox("Общий возраст")
        self.settings_layout.addWidget(self.common_age_checkbox, 2, 0)

        self.progress = QtWidgets.QProgressBar()
        self.settings_layout.addWidget(self.progress, 3, 0, 1, 3)

        self.find_button = QtWidgets.QPushButton("Посмотреть")
        self.settings_layout.addWidget(self.find_button, 3, 3)

        self.setLayout(self.settings_layout)

    def setEnabled(self, mode):
        """
        Метод изменения доступности элементов настроек.
        :param mode: режим доступности
        :type mode: bool
        """
        self.uid_edit.setEnabled(mode)
        self.limit_edit.setEnabled(mode)
        self.likes_friends_checkbox.setEnabled(mode)
        self.likes_self_checkbox.setEnabled(mode)
        self.common_city_checkbox.setEnabled(mode)
        self.common_age_checkbox.setEnabled(mode)
        self.common_friends_checkbox.setEnabled(mode)


class FriendsActivityAnalysisWorker(QtCore.QThread):
    """
    Поток обработки результатов проверки.
    """
    finished = QtCore.pyqtSignal()  # сигнал окончания обработки
    tupleReady = QtCore.pyqtSignal(tuple)  # сигнал получения очередного резульатата

    def __init__(self,
                 vk_session,
                 callback,
                 uid,
                 limit,
                 parent=None,
                 likes_friends_need=False,
                 likes_self_need=False,
                 common_friends_need=False,
                 common_age_need=False,
                 common_city_need=False,
                 friends_full=None):
        """
        Конструктор потока
        :param vk_session: сессия объекта VK
        :param callback: функция, которая выполняется с готовыми результатами
        :param uid: id пользователя, кого проверяем
        :param limit: максимальное количество загружаемых записей
        :param parent: родительский объект
        :param likes_friends_need: проверяем лайки друзьям
        :param likes_self_need: проверяем лайки от друзей
        :param common_friends_need: проверяем общих друзей
        :param common_age_need: проверяем общий возраст
        :param common_city_need: проверяем общий город
        :param friends_full: массив подробной информации обо всех друзьях
        """
        QtCore.QThread.__init__(self, parent)
        self.interest_analysis = ActivityAnalysis.VKActivityAnalysis(vk_session)
        self.tupleReady.connect(callback)
        self.uid = uid
        self.limit = limit
        self.likes_friends_need = likes_friends_need
        self.likes_self_need = likes_self_need
        self.common_friends_need = common_friends_need
        self.common_age_need = common_age_need
        self.common_city_need = common_city_need
        self.friends_full = friends_full
        self.close = False

    def run(self):
        """
        Выполнение потока
        """
        for element in self.interest_analysis.score_all(uid=self.uid,
                                                        limit=self.limit,
                                                        likes_friends_need=self.likes_friends_need,
                                                        likes_self_need=self.likes_self_need,
                                                        common_friends_need=self.common_friends_need,
                                                        common_age_need=self.common_age_need,
                                                        common_city_need=self.common_city_need,
                                                        friends_full=self.friends_full):
            if self.close:
                break
            self.tupleReady.emit(element)
        self.finished.emit()


class FriendsModel(QtWidgets.QTableWidget):
    """
    Модель таблицы с результатами исследования круга общения друзей
    """
    def __init__(self, friends_full=None, parent=None):
        """
        Конструктор модели
        :param friends_full: массив с информацией обо всех друзьях
        :param parent: родительский объект
        """
        super(FriendsModel, self).__init__()
        self.model = []
        self.rows_count = 0
        self.model_sorted = []
        self.headers = {"age": 2, "city": 1, "friends": 3, "likes_self": 4, "likes_friends": 5}
        if friends_full is None:
            return
        self.init_model(friends_full)

    def init_model(self, friends_full):
        """
        Инициализация модели таблицы
        :param friends_full: массив с информацией обо всех друзьях
        """
        self.setRowCount(len(friends_full))
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['Друг',
                                        'Общий город',
                                        'Общий возраст',
                                        'Общие друзья',
                                        'Лайки друзей',
                                        'Лайки у друзей',
                                        'Всего'])
        self.model = []
        for friend in friends_full:
            self.model.append([friend['first_name'] + ' ' + friend['last_name'],
                               0, 0, 0, 0, 0])
        self.rows_count = len(self.model[0])
        self.sort_model()

    def update_all(self):
        """
        Обновляет данные во всех ячейках таблицы
        """
        for i, friend in enumerate(self):
            for j, s in enumerate(friend):
                self.setItem(i, j, QtWidgets.QTableWidgetItem(str(s)))

    def sort_model(self):
        """
        Сортирует строки таблицы по сумме набранных баллов
        """
        self.model_sorted = sorted(self.model,
                                   key=lambda item: sum(item[1:]),
                                   reverse=True)

    def apply(self, row_name, index, value):
        """
        Устанавливает значение в ячейку
        :param row_name: имя колонки
        :param index: номер строки
        :param value: значение
        """
        self.model[index][self.headers[row_name]] = value
        self.sort_model()

    def __iter__(self):
        """
        Инициализация итератора
        :return:
        """
        self.n = 0
        return self

    def __next__(self):
        """
        Следующий элемент при итерации
        """
        if self.n == len(self.model_sorted):
            raise StopIteration
        self.n += 1
        return self.__getitem__(self.n-1)

    def __getitem__(self, item):
        """
        Добавляет ячейку с суммой в таблицу
        :param item: номер строки
        """
        return self.model_sorted[item] + [sum(self.model_sorted[item][1:])]


class FriendsActivityAnalysisWidget(VKModuleDialog):
    """
    Окно модуля исследования круга общения
    """
    def __init__(self, vk, parent=None):
        """
        Конструктор окна
        :param vk: объект класса VK
        :param parent: родительский объект
        """
        super(FriendsActivityAnalysisWidget, self).__init__(vk=vk, parent=parent)
        self.vk = vk
        self.posts = []
        self.initUI()

    def initUI(self):
        """
        Инициализиует интерфейс
        """
        self.setWindowTitle("Изучение круга общения пользователя")
        self.setWindowFlags(QtCore.Qt.Window)
        #self.group_box = QtWidgets.QGroupBox()

        self.view = QtWidgets.QVBoxLayout()

        self.caption = QtWidgets.QLabel("Изучение круга общения")
        self.caption.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.caption.setMaximumHeight(50)
        self.view.addWidget(self.caption)

        self.settings = FriendsActivityAnalysisSettingsWidget()
        self.view.addWidget(self.settings)

        self.results = FriendsModel(friends_full=None)
        self.view.addWidget(self.results)

        #self.setWidget(self.group_box)
        self.setLayout(self.view)
        #self.setWidgetResizable(True)

        self.settings.find_button.clicked.connect(self.get_info)

    def get_info(self, pressed):
        """
        Запускает проверку
        :param pressed: рудимент Qt, не используется
        """

        if self.settings.find_button.text() == 'Остановить':
            self.thread.close = True
            self.finished()
            return

        self.settings.setEnabled(False)
        self.settings.find_button.setText("Остановить")
        self.settings.progress.setValue(0)

        uid = 0
        limit = 0
        try:
            uid = self.get_id_from_link(self.settings.uid_edit.text())
            limit = int(self.settings.limit_edit.text())
        except (ValueError, TypeError):
            VKErrorBox(*VKErrorBox.T_GET_ID_ERR)
            return

        self.activity_analysis = ActivityAnalysis.VKActivityAnalysis(self.vk)
        self.friends_full = self.activity_analysis.friends_all_full(uid=uid)
        self.settings.progress.setMaximum(len(self.friends_full)*(self.settings.likes_friends_checkbox.isChecked()
                                                                  + self.settings.likes_self_checkbox.isChecked()
                                                                  + self.settings.common_friends_checkbox.isChecked()
                                                                  + self.settings.common_age_checkbox.isChecked()
                                                                  + self.settings.common_city_checkbox.isChecked()))

        self.results.init_model(friends_full=self.friends_full)
        self.results.update_all()

        self.thread = FriendsActivityAnalysisWorker(vk_session=self.vk,
                                                    callback=self.add_item,
                                                    uid=uid,
                                                    limit=limit,
                                                    parent=None,
                                                    likes_friends_need=self.settings.likes_friends_checkbox.isChecked(),
                                                    likes_self_need=self.settings.likes_self_checkbox.isChecked(),
                                                    common_friends_need=self.settings.common_friends_checkbox.isChecked(),
                                                    common_age_need=self.settings.common_age_checkbox.isChecked(),
                                                    common_city_need=self.settings.common_city_checkbox.isChecked(),
                                                    friends_full=self.friends_full)
        self.thread.finished.connect(self.finished)
        self.thread.start()

    def add_item(self, item):
        """
        Добавляет очередной результат в таблицу
        :param item: результат проверки
        """
        self.results.apply(*item)
        if item[1] % len(self.friends_full)-1 == 0 \
                or item[0]=='likes_self' \
                or item[0] == 'likes_friends':
            self.results.update_all()
        self.settings.progress.setValue(self.settings.progress.value()+1)

    def finished(self):
        """
        Окончание проверки
        """
        self.settings.setEnabled(True)
        self.settings.find_button.setText("Посмотреть")
        self.results.update_all()