# -*- coding: utf-8 -*-

import os
from subprocess import run
import sys
import time
from threading import Thread
from PyQt5.QtGui import QDesktopServices, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem, \
    QDesktopWidget, QMessageBox, QAction, QFileDialog, QHeaderView, QPushButton, QHBoxLayout, \
    QProgressBar, QAbstractItemView, QLabel
from PyQt5.QtCore import QUrl, Qt, pyqtSignal
from tqdm import tqdm
from whisper import tokenizer, load_model, transcribe
from whisper.utils import get_writer
from app import app_ui
from app import about_ui
from app import progress_ui
from app import resources

__author__ = 'Andrey Izman'
__email__ = 'izmanw@gmail.com'

__DIR__ = os.path.dirname(os.path.realpath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(__DIR__, 'output')
MODELS_DIR = os.path.join(__DIR__, 'models')


# from PyQt5 import uic
# def setupUI(parent, ui):
#     parent.ui = uic.loadUi(os.path.join(__DIR__, ui + '.ui'), parent)


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

        self.ui = about_ui.Ui_Form()
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


class ProgressWindow(CenteredWindow):
    progressSignal = pyqtSignal(int, int, str, str, str, str)
    is_done = False

    def __init__(self, parent):
        super(ProgressWindow, self).__init__(parent)
        self.parent = parent

        # setupUI(self, 'progress')
        self.ui = progress_ui.Ui_Form()
        self.ui.setupUi(self)

        text = f'Downloading model "{parent.model}"...'
        self.setWindowTitle(text)
        self.ui.text.setText(text)
        self.ui.fmt.setText('')
        self.ui.rate.setText('')
        self.ui.remaining.setText('')
        self.ui.cancelBtn.clicked.connect(self.close)
        self.progressSignal.connect(self.updateProgress)

    def updateProgress(self, n, total, fmt, elapsed, remaining, rate):
        if n >= total:
            if not self.is_done:
                self.is_done = True
                self.close()
                self.parent.downloadProgress = None
            return
        self.ui.progressBar.setValue(n)
        self.ui.progressBar.setMaximum(total)
        self.ui.fmt.setText(fmt)
        self.ui.rate.setText(rate)
        self.ui.remaining.setText(f'Elapsed: {elapsed}  Remaining: {remaining}')

    def closeEvent(self, event):
        if not self.is_done:
            self.parent.cancel()


class DownloaderProgressBar(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current = self.n
        # self.disable = True

    @staticmethod
    def _format_meter(n, total, elapsed, unit='it', unit_scale=False, rate=None, postfix=None,
                      unit_divisor=1000, initial=0, **extra_kwargs):
        # sanity check: total
        if total and n >= (total + 0.5):  # allow float imprecision (#849)
            total = None

        # apply custom scale if necessary
        if unit_scale and unit_scale not in (True, 1):
            if total:
                total *= unit_scale
            n *= unit_scale
            if rate:
                rate *= unit_scale  # by default rate = self.avg_dn / self.avg_dt
            unit_scale = False

        elapsed_str = tqdm.format_interval(elapsed)

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = (n - initial) / elapsed
        inv_rate = 1 / rate if rate else None
        format_sizeof = tqdm.format_sizeof
        rate_noinv_fmt = ((format_sizeof(rate) if unit_scale else
                           '{0:5.2f}'.format(rate)) if rate else '?') + unit + '/s'
        rate_inv_fmt = (
            (format_sizeof(inv_rate) if unit_scale else '{0:5.2f}'.format(inv_rate))
            if inv_rate else '?') + 's/' + unit
        rate_fmt = rate_inv_fmt if inv_rate and inv_rate > 1 else rate_noinv_fmt

        if unit_scale:
            n_fmt = format_sizeof(n, divisor=unit_divisor)
            total_fmt = format_sizeof(total, divisor=unit_divisor) if total is not None else '?'
        else:
            n_fmt = str(n)
            total_fmt = str(total) if total is not None else '?'

        try:
            postfix = ', ' + postfix if postfix else ''
        except TypeError:
            pass

        remaining = (total - n) / rate if rate and total else 0
        remaining_str = tqdm.format_interval(remaining) if rate else '?'

        return f'{n_fmt}/{total_fmt}', elapsed_str, remaining_str, f'{rate_fmt}{postfix}'

    def update(self, n=1):
        global window
        super().update(n)
        self._current += n
        fmt, elapsed, remaining, rate = self._format_meter(**self.format_dict)

        n = self._current
        total = self.total
        while total >= 0x7FFFFFFF:
            total = round(total / 100)
            n = round(n / 100)

        window.downloadProgressSignal.emit(n, total, fmt, elapsed, remaining, rate)
        return True


whisper_module = sys.modules['whisper']
whisper_module.tqdm = DownloaderProgressBar


class TranscribeProgressBar(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current = self.n
        # self.disable = False

    def update(self, n=1):
        global window
        # super().update(n)
        self._current += n

        n = self._current
        total = self.total
        while total >= 0x7FFFFFFF:
            total = round(total / 100)
            n = round(n / 100)

        window.updateProgressSignal.emit(n, total)
        return True


transcribe_module = sys.modules['whisper.transcribe']
transcribe_module.tqdm.tqdm = TranscribeProgressBar


class MessageBox:
    def __init__(self, text, title=None, info=None, icon=QMessageBox.Critical):
        msg = QMessageBox()
        msg.setIcon(icon if icon else QMessageBox.Critical)
        msg.setText(text)
        if info:
            msg.setInformativeText(info)
        msg.setWindowTitle(title if title else text)
        msg.exec_()


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
    progressBar = None
    running = False
    execThread = None
    spacer1 = None
    spacer2 = None
    has_ffmpeg = True
    downloadProgress = None
    downloadProgressSignal = pyqtSignal(int, int, str, str, str, str)
    updateProgressSignal = pyqtSignal(int, int)
    prepareProgressSignal = pyqtSignal(str)
    reloadListSignal = pyqtSignal()
    removeFileSignal = pyqtSignal(str)
    execNextSignal = pyqtSignal()
    errorSignal = pyqtSignal(object)

    def __init__(self):
        super(AppWindow, self).__init__()
        self.initMenu()
        # setupUI(self, 'app')
        self.ui = app_ui.Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle('Whisper QT')
        self.initDefaults()
        self.initUi()
        self.initSignals()
        self.show()
        self.center()

        cmd = ["ffmpeg", "-version"]
        try:
            run(cmd, capture_output=True, check=True).stdout
        except:
            self.has_ffmpeg = False
            MessageBox('Fatal error', info='ffmpeg is not installed! ffmpeg is required to be installed')

    def initDefaults(self):
        self.model = 'small'
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
        # self.removeIcon = QPixmap(":/ui/img/entry-delete.svg")
        self.removeIcon = QPixmap(":/ui/img/cancel-white.svg")
        icon = QPixmap(":/ui/img/start.svg")
        self.ui.runBtn.setIcon(QIcon(icon))
        self.ui.runBtn.setEnabled(False)
        icon = QPixmap(":/ui/img/add.svg")
        self.ui.addBtn.setIcon(QIcon(icon))
        # self.setWindowIcon(QIcon(':/ui/img/openai.png'))
        self.setWindowIcon(QIcon(':/ui/img/openai_logo.svg'))
        icon = QPixmap(":/ui/img/folder.svg")
        self.ui.chooseDirBtn.setIcon(QIcon(icon))

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

    def initSignals(self):
        self.ui.chooseDirBtn.clicked.connect(self.browseDir)
        self.ui.addBtn.clicked.connect(self.browseFiles)
        self.ui.modelCombo.currentIndexChanged.connect(self.modelChanged)
        self.ui.languageCombo.currentIndexChanged.connect(self.languageChanged)
        self.ui.formatCombo.currentIndexChanged.connect(self.formatChanged)
        self.ui.deviceCombo.currentIndexChanged.connect(self.deviceChanged)
        self.ui.taskCombo.currentIndexChanged.connect(self.taskChanged)
        self.ui.runBtn.clicked.connect(self.run)
        self.prepareProgressSignal.connect(self.createProgress)
        self.removeFileSignal.connect(self.removeClicked)
        self.execNextSignal.connect(self.execNext)
        self.downloadProgressSignal.connect(self.updateDownloadProgress)
        self.updateProgressSignal.connect(self.updateProgress)
        self.reloadListSignal.connect(self.reloadList)
        self.errorSignal.connect(self.on_error)

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
        files, _ = QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select one or more files to open",
            # __DIR__,
            filter=f'Audio files ({audioFormats});;All files (*.*)')
        if files:
            self.add_files = files
            self.updateList()

    def browseDir(self):
        open_dir = QFileDialog.getExistingDirectory(self, "Select output directory")
        if open_dir:
            self.output_dir = open_dir
            self.ui.outputDirEdit.setText(self.output_dir)

    def initTable(self):
        if not self.tableWidget:
            self.files = []
            self.removeSpacer()
            self.tableWidget = QTableWidget()
            self.tableWidget.verticalHeader().setVisible(False)
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem('Filename'))
            self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem('Size'))
            self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem('Remove'))
            self.tableWidget.horizontalHeader().setDefaultSectionSize(140)
            self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.tableWidget.setSortingEnabled(False)
            self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            # select row
            self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
            # no selection
            # self.tableWidget.setFocusPolicy(Qt.NoFocus)
            # self.tableWidget.setSelectionMode(QAbstractItemView.NoSelection)

            self.ui.tableLayout.addWidget(self.tableWidget)

    def removeClicked(self, file):
        idx = self.files.index(file)
        self.tableWidget.setSpan(idx, 0, 1, 1)
        self.tableWidget.setSpan(idx, 0, 2, 1)
        self.tableWidget.setSpan(idx, 0, 3, 1)
        self.tableWidget.removeRow(idx)
        del self.files[idx]
        if not self.files:
            self.updateList()

    def addTableFiles(self):
        files_len = len(self.files) + len(self.add_files)
        self.tableWidget.setRowCount(files_len)
        for i, file in enumerate(self.add_files):
            if file in self.files:
                files_len -= 1
                self.tableWidget.setRowCount(files_len)
                continue
            idx = len(self.files)
            self.files.append(file)
            self.tableWidget.setItem(idx, 0, QTableWidgetItem(file))
            self.tableWidget.setItem(idx, 1, QTableWidgetItem(strBytes(getFileSize(file))))
            widget = QWidget()
            btn = QPushButton()
            btn.setObjectName(f'remove_{idx}')
            btn.setIcon(QIcon(self.removeIcon))
            ffile = file.replace('"', '\\"')
            btn.clicked.connect(eval(f'lambda: self.removeClicked("{ffile}")', {'self': self}))
            layout = QHBoxLayout()
            layout.addWidget(btn)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            self.tableWidget.setCellWidget(idx, 2, widget)
        self.add_files = None

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
            if not self.running:
                self.ui.runBtn.setEnabled(True)
        else:
            self.files = []
            self.ui.runBtn.setEnabled(False)
            if self.tableWidget:
                b = self.ui.tableLayout.takeAt(0)
                b.widget().deleteLater()
                # self.ui.tableLayout.removeWidget(self.tableWidget)
                self.tableWidget = None
                self.addSpacer()

    def reloadList(self):
        files = list(self.files)
        for file in files:
            self.removeClicked(file)
        self.add_files = files
        self.updateList()

    def run(self):
        if self.has_ffmpeg and not self.running:
            self.running = True
            # self.ui.runBtn.setEnabled(False)
            self.setEnabledUI(False)
            self.execThread = Thread(target=self.exec)
            self.execThread.start()

    def updateProgress(self, current, maximum):
        self.progressBar.setMaximum(maximum)
        self.progressBar.setValue(current)

    def updateDownloadProgress(self, n, total, fmt, elapsed, remaining, rate):
        if not self.downloadProgress:
            self.downloadProgress = ProgressWindow(self)
            self.downloadProgress.show()
            self.downloadProgress.center()
        self.downloadProgress.progressSignal.emit(n, total, fmt, elapsed, remaining, rate)

    def execNext(self):
        if self.files:
            # print('run next')
            self.execThread = Thread(target=self.exec)
            self.execThread.start()
        else:
            # print('done')
            self.running = False
            self.setEnabledUI(True)
            MessageBox('Successfully completed', icon=QMessageBox.Information)

    def createProgress(self, file):
        emptyTWidget0 = QTableWidgetItem()
        emptyTWidget1 = QTableWidgetItem()
        emptyTWidget2 = QTableWidgetItem()
        emptyWidget = QWidget()
        progressWidget = QWidget()
        progressBar = QProgressBar()
        progressBar.setFixedWidth(220)
        layout = QHBoxLayout()

        # Join 3 cols and put progress with file name
        label = QLabel()
        label.setText(file)
        layout.addWidget(label)

        layout.addWidget(progressBar)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(5, 0, 5, 0)
        progressWidget.setLayout(layout)

        # Join 3 cols and put progress with file name
        self.tableWidget.setItem(0, 0, emptyTWidget0)

        self.tableWidget.setItem(0, 1, emptyTWidget1)
        self.tableWidget.setItem(0, 2, emptyTWidget2)
        self.tableWidget.setCellWidget(0, 2, emptyWidget)
        # self.tableWidget.setSpan(0, 1, 1, 2)
        # self.tableWidget.setCellWidget(0, 1, progressWidget)

        # Join 3 cols and put progress with file name
        self.tableWidget.setSpan(0, 0, 1, 3)
        self.tableWidget.setCellWidget(0, 0, progressWidget)

        self.progressBar = progressBar

    def on_error(self, error):
        print(error)
        self.running = False
        self.setEnabledUI(True)
        self.reloadListSignal.emit()
        MessageBox('Error', info=str(error))

    def exec(self):
        if self.files:
            def on_err(error):
                self.errorSignal.emit(error)
            try:
                try:
                    file = self.files[0]
                    self.prepareProgressSignal.emit(file)
                    self.transcribe(file)
                    self.removeFileSignal.emit(file)
                    time.sleep(0.05)
                    self.execNextSignal.emit()
                except FileNotFoundError as err:
                    on_err(err)
                except AssertionError as err:
                    on_err(err)
                except RuntimeError as err:
                    on_err(err)
            except Exception as err:
                on_err(err)

    def transcribe(self, file):
        file_name = os.path.basename(file)
        name = os.path.splitext(file_name)[0]
        output_dir = os.path.join(self.output_dir, name)
        os.makedirs(output_dir, exist_ok=True)
        model = load_model(self.model, device=self.device, download_root=MODELS_DIR)
        writer = get_writer(self.format, output_dir)
        language = self.language if self.language != 'auto' else None
        result = transcribe(model, file, fp16=False, verbose=None, language=language, task=self.task)
        opt = {"max_line_width": 200, "max_line_count": 20000, "highlight_words": False}
        writer(result, file, options=opt)

    def setEnabledUI(self, enabled=True):
        self.ui.runBtn.setEnabled(enabled and bool(self.files))
        self.ui.chooseDirLabel.setEnabled(enabled)
        self.ui.outputDirEdit.setEnabled(enabled)
        self.ui.chooseDirBtn.setEnabled(enabled)
        self.ui.modelLabel.setEnabled(enabled)
        self.ui.modelCombo.setEnabled(enabled)
        self.ui.languageLabel.setEnabled(enabled)
        self.ui.languageCombo.setEnabled(enabled)
        self.ui.formatLabel.setEnabled(enabled)
        self.ui.formatCombo.setEnabled(enabled)
        self.ui.deviceLabel.setEnabled(enabled)
        self.ui.deviceCombo.setEnabled(enabled)
        self.ui.taskLabel.setEnabled(enabled)
        self.ui.taskCombo.setEnabled(enabled)

    def cancel(self):
        self.downloadProgress = None
        self.running = False
        self.setEnabledUI(True)
        self.reloadListSignal.emit()
        if self.execThread:
            self.execThread._stop()

    def close(self):
        if self.execThread:
            self.execThread._stop()

        super(AppWindow, self).close()

    def closeEvent(self, event):
        if self.execThread:
            self.execThread._stop()


window = None


def main():
    global window
    app = QApplication(sys.argv)
    app.setStyleSheet(CSS)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
