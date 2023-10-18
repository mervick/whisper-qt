# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'about.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(450, 300)
        self.widget = QtWidgets.QWidget(Form)
        self.widget.setGeometry(QtCore.QRect(0, 0, 450, 300))
        self.widget.setObjectName("widget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.widget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 450, 300))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setGeometry(QtCore.QRect(0, 0, 450, 300))
        self.label.setObjectName("label")
        self.aboutLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.aboutLabel.setGeometry(QtCore.QRect(0, 180, 450, 120))
        self.aboutLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.aboutLabel.setObjectName("aboutLabel")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "About"))
        self.label.setText(_translate("Form", "<html><head/><body><p align=\"center\"><img src=\":/ui/img/whisper-450.png\" width=\"450\" height=\"300\"/></p></body></html>"))
        self.aboutLabel.setText(_translate("Form", "<html><head/><body><p align=\"center\"><a href=\"https://github.com/mervick/whisper-qt\"><span style=\" font-size:10pt; text-decoration: underline; color:#ffffff;\">Whisper QT 1.0</span></a></p><p align=\"center\"><span style=\" font-size:10pt; color:#ffffff;\">Licensed under MIT and LGPL v3</span></p><p align=\"center\"><span style=\" font-size:9pt; color:#ffffff;\">Copyright © 2023 OpenAI, Andrey Izman and others, see COPYING.txt</span></p></body></html>"))



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())