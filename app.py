# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices, QResizeEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QTableWidget, QTableWidgetItem, \
    QDesktopWidget, QTabWidget, QVBoxLayout, QSizePolicy, QMessageBox, QAction, QFileDialog, QHeaderView, QSpacerItem, \
    QPushButton, QHBoxLayout
from PyQt5.QtCore import QSize, Qt, QThread, QObject, pyqtSignal, pyqtSlot, QEvent
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import uic
import ui as UI
from whisper import tokenizer

__author__ = 'Andrey Izman'
__email__ = 'izmanw@gmail.com'

__DIR__ = os.path.dirname(os.path.realpath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(__DIR__, 'output')


def setupUI(parent, ui):
    parent.ui = uic.loadUi(os.path.join(__DIR__, 'ui', ui + '.ui'), parent)
    # parent.ui = uic.loadUi(__DIR__ + '/ui/' + ui + '.ui', parent)


class CenteredWindow(QMainWindow):
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class AboutWindow(CenteredWindow):
    def mousePressEvent(self, event):
        QDesktopServices.openUrl(QUrl('https://github.com/mervick/whisper-qt'))

    def __init__(self, parent):
        super(AboutWindow, self).__init__(parent)

        self.ui = UI.about.Ui_Form()
        self.ui.setupUi(self)

        # setupUI(self, 'about')
        # self.ui = uic.loadUi('/home/izman/about.ui', self)
        self.setWindowTitle('About Whisper QT')
        self.ui.aboutLabel.mousePressEvent = self.mousePressEvent
        self.setFixedSize(450, 300)

        # self.ui.label.setText(self.ui.label.text() % __version__)
        # self.ui.label.mousePressEvent = lambda a: self.close()
        # self.ui.okBtn.clicked.connect(self.close)
        # self.show()
        self.center()


LANGUAGES = ('auto', *tokenizer.LANGUAGES.values())
MODELS = ('tiny', 'base', 'small', 'medium', 'large')
FORMATS = ("txt", "vtt", "srt", "tsv", "json", "all")
DEVICES = ('cpu', 'cuba')
TASKS = ('transcribe', 'translate')
AUDIO_EXTENSIONS = ('aac', 'wma', 'flac', 'mp3', 'mp4', 'ogg', 'cda', 'midi', 'mpga', 'opus', 'wav', '3gp', '3g2',
                    'aiff', 'au', 'pcm', 'm4a')


CSS = '''
QTableWidget QPushButton {
    color: #fff;
    background-color: #dc3545;
}
QTableWidget QPushButton:hover {
    /* background-color: #bb2d3b; */
    background-color: #c82333;
    border-color: #bd2130;
}
QTableWidget QPushButton:pressed {
    /* border: 1px solid #f0a9b0; */
    background-color: #bd2130;
    border-color: #b21f2d;
}
'''


def getFileSize(file):
    try:
        return os.path.getsize(file)
    except FileNotFoundError:
        print("File not found.")
    except OSError:
        print("OS error occurred.")
    return 0


def strBytes(val, type='decimal'):
    # type - decimal or binary
    k = 1000 if type == 'decimal' else 1024
    n = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if type != 'decimal':
        n = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB']
    j = 1
    while val > pow(k, j) and j < len(n):
        j += 1
    s = n[j - 1]
    num = val / pow(k, j - 1)
    return f"{num:.2f} {s}"


class AppWindow(CenteredWindow):
    model = None
    language = None
    format = None
    device = None
    task = None
    output_dir = None
    tableWidget = None
    removeIcon = None
    add_files = None
    files = None

    def __init__(self):
        super(AppWindow, self).__init__()
        # setupUI(self, 'main')
        setupUI(self, 'app-ext')
        self.setWindowTitle('Whisper QT')
        self.initDefaults()
        self.initMenu()
        self.initUi()
        self.show()
        self.center()

    def initDefaults(self):
        self.model = 'medium'
        self.language = 'auto'
        self.format = 'txt'
        self.device = 'cpu'
        self.task = 'transcribe'
        self.output_dir = DEFAULT_OUTPUT_DIR

    def aboutDialog(self):
        win = AboutWindow(self)
        win.show()
        win.center()

    def initUi(self):
        # set btn icons
        # self.removeIcon = QtGui.QPixmap(":/ui/img/entry-delete.svg")
        self.removeIcon = QtGui.QPixmap(":/ui/img/cancel-white.svg")
        icon = QtGui.QPixmap(":/ui/img/start.svg")
        self.ui.runBtn.setIcon(QtGui.QIcon(icon))
        self.ui.runBtn.setEnabled(False)
        icon = QtGui.QPixmap(":/ui/img/add.svg")
        self.ui.addBtn.setIcon(QtGui.QIcon(icon))
        # self.setWindowIcon(QIcon(':/ui/img/openai.png'))
        self.setWindowIcon(QIcon(':/ui/img/openai_logo.svg'))
        icon = QtGui.QPixmap(":/ui/img/folder.svg")
        self.ui.chooseDirBtn.setIcon(QtGui.QIcon(icon))

        # init combo options, set default values
        self.ui.modelCombo.addItems(MODELS)
        self.ui.modelCombo.setCurrentIndex(MODELS.index(self.model))
        self.ui.languageCombo.addItems(LANGUAGES)
        self.ui.languageCombo.setCurrentIndex(LANGUAGES.index(self.language))
        self.ui.formatCombo.addItems(FORMATS)
        self.ui.formatCombo.setCurrentIndex(FORMATS.index(self.format))
        self.ui.deviceCombo.addItems(DEVICES)
        self.ui.deviceCombo.setCurrentIndex(DEVICES.index(self.device))
        self.ui.taskCombo.addItems(TASKS)
        self.ui.taskCombo.setCurrentIndex(TASKS.index(self.task))
        self.ui.outputDirEdit.setText(self.output_dir)

        # connect signals
        self.ui.chooseDirBtn.clicked.connect(self.browseDir)
        self.ui.addBtn.clicked.connect(self.browseFiles)
        # self.tableWidget = QTableWidget()
        # self.ui.tableLayout.addWidget(self.tableWidget)
        self.modelCombo.currentIndexChanged.connect(self.modelChanged)
        self.languageCombo.currentIndexChanged.connect(self.languageChanged)
        self.formatCombo.currentIndexChanged.connect(self.formatChanged)
        self.deviceCombo.currentIndexChanged.connect(self.deviceChanged)
        self.taskCombo.currentIndexChanged.connect(self.taskChanged)

    def modelChanged(self, index):
        self.model = MODELS[index]

    def languageChanged(self, index):
        self.language = LANGUAGES[index]

    def formatChanged(self, index):
        self.format = FORMATS[index]

    def deviceChanged(self, index):
        self.device = DEVICES[index]

    def taskChanged(self, index):
        self.task = TASKS[index]

    def initMenu(self):
        menuBar = self.menuBar()
        menu = menuBar.addMenu("File")
        action = QAction('Exit', self)
        action.triggered.connect(self.close)
        menu.addAction(action)
        menuBar = self.menuBar()
        menu = menuBar.addMenu("Help")
        action = QAction('About', self)
        action.triggered.connect(self.aboutDialog)
        menu.addAction(action)

    def browseFiles(self):
        audioFormats = ' '.join(list(map(lambda a: f'*.{a}', list(AUDIO_EXTENSIONS))))
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select one or more files to open",
            # __DIR__,
            filter=f'Audio files ({audioFormats});;All files (*.*)')
        print(files)
        if files:
            self.add_files = files
            self.updateList()
        # print(self.ui.findChild(QSpacerItem, "verticalSpacer"))
        print(self.ui.findChild(QSpacerItem))

        for i in range(0, 2):
            widget = self.ui.verticalLayout.itemAt(i).widget()
            print(widget)

    def browseDir(self):
        open_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select output directory")
        if open_dir:
            self.output_dir = dir
            self.ui.outputDirEdit.setText(self.output_dir)

    def initTable(self):
        if not self.tableWidget:
            self.removeSpacer()
            self.files = []
            self.tableWidget = QTableWidget()
            self.tableWidget.verticalHeader().setVisible(False)
            self.ui.tableLayout.addWidget(self.tableWidget)
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem('Filename'))
            self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem('Size'))
            self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem('Remove'))
            self.tableWidget.horizontalHeader().setDefaultSectionSize(140)
            self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def removeClicked(self, event):
        print('remove %s' % event)

    def addTableFiles(self):
        self.tableWidget.setRowCount(len(self.files) + len(self.add_files))
        for i, file in enumerate(self.add_files):
            print(file)
            idx = len(self.files)
            print(f'idx: {idx}')
            self.files.append(file)
            self.tableWidget.setItem(idx, 0, QTableWidgetItem(file))
            self.tableWidget.setItem(idx, 1, QTableWidgetItem(strBytes(getFileSize(file))))
            widget = QWidget()
            btn = QPushButton()
            btn.setObjectName(f'remove_{idx}')
            btn.setIcon(QtGui.QIcon(self.removeIcon))
            ffile = file.replace('"', '\\"')
            btn.clicked.connect(eval(f'lambda: self.removeClicked("{ffile}")', {'self': self}))
            layout = QHBoxLayout()
            layout.addWidget(btn)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            self.tableWidget.setCellWidget(idx, 2, widget)

    def removeSpacer(self):
        self.spacer1 = self.ui.verticalLayout.itemAt(0)
        self.spacer2 = self.ui.verticalLayout.itemAt(2)
        self.ui.verticalLayout.removeItem(self.spacer1)
        self.ui.verticalLayout.removeItem(self.spacer2)

    def addSpacer(self):
        self.ui.verticalLayout.insertSpacerItem(0, self.spacer1)
        self.ui.verticalLayout.insertSpacerItem(2, self.spacer2)

    def updateList(self):
        if self.add_files:
            self.initTable()
            self.addTableFiles()
            self.ui.runBtn.setEnabled(True)
        else:
            self.files = []
            self.ui.runBtn.setEnabled(False)
            if self.tableWidget:
                self.ui.tableLayout.removeWidget(self.tableWidget)
                self.tableWidget = None
                self.addSpacer()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(CSS)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
