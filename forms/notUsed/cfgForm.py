# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cfg.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 161)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 371, 101))
        self.groupBox.setObjectName("groupBox")
        self.Create = QtWidgets.QRadioButton(self.groupBox)
        self.Create.setGeometry(QtCore.QRect(10, 40, 181, 26))
        self.Create.setChecked(True)
        self.Create.setObjectName("Create")
        self.Load = QtWidgets.QRadioButton(self.groupBox)
        self.Load.setGeometry(QtCore.QRect(10, 70, 181, 26))
        self.Load.setObjectName("Load")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(285, 120, 91, 28))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "Experiment configuration file"))
        self.Create.setText(_translate("Dialog", "Create configuration file"))
        self.Load.setText(_translate("Dialog", "Load configuration file"))

