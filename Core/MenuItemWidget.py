from PyQt5 import QtWidgets, QtGui, QtCore
import os


class VKMenuItemWidget(QtWidgets.QLabel):
    """
    Элмент меню главного окна
    """
    clicked = QtCore.pyqtSignal(str)

    def __init__(self, name):
        super(VKMenuItemWidget, self).__init__()
        self.name = name
        path = os.path.join(os.path.dirname(__file__), 'images/')
        std_img_path = os.path.join(path, name + '_btn_0.PNG')
        hover_img_path = os.path.join(path, name + '_btn_1.PNG')
        pressed_img_path = os.path.join(path, name + '_btn_2.PNG')
        self.std_img = QtGui.QPixmap()
        self.hover_img = QtGui.QPixmap()
        self.pressed_img = QtGui.QPixmap()
        if os.path.isfile(std_img_path) and os.path.isfile(hover_img_path) and os.path.isfile(pressed_img_path):
            self.std_img.loadFromData(open(std_img_path, 'rb').read())
            self.hover_img.loadFromData(open(hover_img_path, 'rb').read())
            self.pressed_img.loadFromData(open(pressed_img_path, 'rb').read())
        else:
            raise IOError("Resource files not found for " + std_img_path)
        self.setPixmap(self.std_img)

    # Qt DoubleClick fix

    def mousePressEvent(self, QMouseEvent):
        super().mousePressEvent(QMouseEvent)
        self.state = 1
        self.setPixmap(self.pressed_img)

    def performSingleClickAction(self):
        if self.state == 1:
            self.clicked.emit(self.name)

    def mouseDoubleClickEvent(self, QMouseEvent):
        self.state = 2
        self.setPixmap(self.pressed_img)
        self.clicked.emit(self.name)

    def mouseReleaseEvent(self, QMouseEvent):
        super().mousePressEvent(QMouseEvent)
        self.setPixmap(self.hover_img)
        if self.state == 1:
            QtCore.QTimer.singleShot(QtWidgets.QApplication.instance().doubleClickInterval(), self.performSingleClickAction)

    def enterEvent(self, *args, **kwargs):
        super().enterEvent(*args, **kwargs)
        self.setPixmap(self.hover_img)

    def leaveEvent(self, *args, **kwargs):
        super().leaveEvent(*args, **kwargs)
        self.setPixmap(self.std_img)
