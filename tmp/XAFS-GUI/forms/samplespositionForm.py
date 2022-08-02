# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'samplesposition.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(346, 654)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(250, 20, 81, 241))
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.samplepositions = QtWidgets.QTableWidget(Dialog)
        self.samplepositions.setGeometry(QtCore.QRect(10, 20, 221, 601))
        self.samplepositions.setObjectName("samplepositions")
        self.samplepositions.setColumnCount(2)
        self.samplepositions.setRowCount(1)
        item = QtWidgets.QTableWidgetItem()
        self.samplepositions.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.samplepositions.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.samplepositions.setHorizontalHeaderItem(1, item)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Sample positions"))
        item = self.samplepositions.verticalHeaderItem(0)
        item.setText(_translate("Dialog", "1"))
        item = self.samplepositions.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "X"))
        item = self.samplepositions.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "Y"))

