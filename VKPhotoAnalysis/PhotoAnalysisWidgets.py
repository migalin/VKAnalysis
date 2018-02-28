from PyQt5 import QtCore, QtWidgets, QtGui
from VKPhotoAnalysis import PhotoClassifier
import vk_api
from queue import Queue
from Core.CoreClasses import VKModuleDialog, VKErrorBox


class PhotoAnalysisWorker(QtCore.QThread):
    """
    Поток для получения результатов проверки
    """
    finished = QtCore.pyqtSignal()
    dictReady = QtCore.pyqtSignal(dict)

    def __init__(self, vk_session, queue, callback, parent=None):
        """
        Конструктор потока
        :param vk_session: объект VK
        :param queue: очередь картинок
        :param callback: функция, которая выполняет действия с результатом
        :param parent: родительский класс
        """
        QtCore.QThread.__init__(self, parent)
        self.queue = queue
        self.photo_analysis = PhotoClassifier.Classifier(vk_session)
        self.dictReady.connect(callback)
        self.close = False

    def run(self):
        """
        Работа потока
        """
        while not self.close:
            arg = self.queue.get()
            if arg is None:
                del self.photo_analysis
                self.finished.emit()
                return
            score = self.photo_analysis.check_photo(arg)
            self.dictReady.emit(score)


class PhotoAnalysisWidget(VKModuleDialog):
    """
    Виджет проверки фото на наличие NSFW контента
    """
    PHOTO_MAX_GET_WALL = 100
    START_SCALE = 256

    def __init__(self, vk, parent=None):
        super(PhotoAnalysisWidget, self).__init__(parent)
        self.setMinimumHeight(600)

        self.setWindowFlags(QtCore.Qt.Window)
        self.vk = vk
        self.tools = vk_api.VkTools(self.vk)

        self.setWindowTitle("VK NSFW Photo Analisys")
        self.threads = []

        self.mygroupbox = QtWidgets.QGroupBox()
        self.myform = QtWidgets.QFormLayout()

        self.mygroupbox.setLayout(self.myform)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.settings_layout = QtWidgets.QHBoxLayout(self)
        self.uid_caption = QtWidgets.QLabel("ID/Ссылка:")
        self.uid_caption.sizeHint()
        self.uid_edit = QtWidgets.QLineEdit()
        self.uid_edit.setMinimumWidth(150)
        self.limit_caption = QtWidgets.QLabel("Лимит загрузки фото:")
        self.limit_caption.sizeHint()
        self.limit_edit = QtWidgets.QLineEdit()
        self.limit_edit.setMinimumWidth(30)
        self.limit_edit.setText("100")
        self.threads_caption = QtWidgets.QLabel("Потоков:")
        self.threads_caption.sizeHint()
        self.threads_edit = QtWidgets.QLineEdit()
        self.threads_edit.setText("2")
        self.threads_edit.setMinimumWidth(30)
        self.all_photos_checkbox = QtWidgets.QCheckBox("Все фото")
        self.all_photos_checkbox.sizeHint()
        self.all_photos_checkbox.setChecked(False)
        self.settings_layout.addWidget(self.uid_caption)
        self.settings_layout.addWidget(self.uid_edit)
        self.settings_layout.addWidget(self.limit_caption)
        self.settings_layout.addWidget(self.limit_edit)
        self.settings_layout.addWidget(self.threads_caption)
        self.settings_layout.addWidget(self.threads_edit)
        self.settings_layout.addWidget(self.all_photos_checkbox)

        self.scale_layout = QtWidgets.QHBoxLayout()
        self.scale_caption = QtWidgets.QLabel("Масштаб")
        self.scale = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.scale.setMinimum(64)
        self.scale.setMaximum(640)
        self.scale.setSingleStep(10)
        self.scale.setValue(self.START_SCALE)
        self.scale.valueChanged.connect(self.scale_changed)
        self.scale_layout.addWidget(self.scale_caption)
        self.scale_layout.addWidget(self.scale)

        self.button = QtWidgets.QPushButton("Проверить фотографии пользователя", self)
        self.button.setToolTip("Запустить проверку")
        self.button.clicked.connect(self.run)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setMinimum(0)

        self.list = QtWidgets.QListWidget(self)
        self.list.setViewMode(QtWidgets.QListView.IconMode)
        self.list.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.list.setDragDropMode(0)
        self.list.setIconSize(QtCore.QSize(self.START_SCALE, self.START_SCALE))
        self.list.setSizeAdjustPolicy(QtWidgets.QListWidget.AdjustToContents)

        self.layout.addLayout(self.settings_layout)
        self.layout.addLayout(self.scale_layout)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.list)

    def set_enabled(self, enabled):
        self.all_photos_checkbox.setEnabled(enabled)
        if enabled:
            self.button.setText("Проверить фотографии пользователя")
        else:
            self.button.setText("Отмена")
        self.threads_edit.setEnabled(enabled)
        self.limit_edit.setEnabled(enabled)
        self.uid_edit.setEnabled(enabled)

    def delete_posts(self):
        self.list.clear()

    def run(self):
        if self.button.text() == "Отмена":
            for thread in self.threads:
                thread.close = True
            # self.threads = []
            self.set_enabled(True)
            return
        try:
            uid = self.get_id_from_link(self.uid_edit.text())
            limit = int(self.limit_edit.text())
            threads_count = min(int(self.threads_edit.text()), 3)
            self.set_enabled(False)
        except (ValueError, TypeError):
            VKErrorBox(*VKErrorBox.T_GET_ID_ERR)
            print('err')
            return
        self.delete_posts()

        # TODO: ВОТ ЭТО ВСЕ В ПОТОК УБРАТЬ!!!! не знаю, зачем это здесь...
        photos = self.tools.get_all('photos.getAll',
                           max_count=self.PHOTO_MAX_GET_WALL,
                           values={'owner_id': uid, 'no_service_albums': 0},
                           key='items',
                           limit=limit
                           )
        photos_wall = self.tools.get_all('photos.get',
                                    max_count=1000,
                                    values={'owner_id': uid, 'album_id': 'wall'},
                                    key='items',
                                    limit=limit
                                    )
        photos_saved = self.tools.get_all('photos.get',
                                         max_count=1000,
                                         values={'owner_id': uid, 'album_id': 'saved'},
                                         key='items',
                                         limit=limit
                                         )
        photos['items'] += photos_wall['items'] + photos_saved['items']
        photo_urls = [el['photo_604'] for el in photos['items'] if 'photo_604' in el]
        self.progress.setMaximum(min(len(photo_urls), limit))
        self.count_proceed = 0

        if not photo_urls:
            self.set_enabled(True)
            return
        self.queue = Queue()
        self.threads = []
        for i in range(threads_count):
            thread = PhotoAnalysisWorker(vk_session=self.vk,
                                         queue=self.queue,
                                         callback=self.add_photo_to_grid
                                         )
            self.threads.append(thread)
            thread.start()

        for el in photo_urls[:min(len(photo_urls),limit)]:
            self.queue.put(el)

        for _ in range(threads_count):
            self.queue.put(None)

    def add_photo_to_grid(self, data):  # Вызывается для обработки сигнала
        self.count_proceed += 1
        self.progress.setValue(self.count_proceed)
        score = round(data['score']*100)
        if score > 20 or self.all_photos_checkbox.isChecked():
            item = QtWidgets.QListWidgetItem()
            item.setText(str(score) + "%")
            icon = QtGui.QIcon()
            pix = QtGui.QPixmap()
            pix.loadFromData(data['picture'])
            icon.addPixmap(pix, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            item.setIcon(icon)
            self.list.addItem(item)
        if self.progress.maximum() == self.count_proceed:
            self.set_enabled(True)

    def scale_changed(self, value):
        self.list.setIconSize(QtCore.QSize(value,value))
