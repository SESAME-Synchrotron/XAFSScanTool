# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ExperimentType.ui'
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
        self.UsersExp = QtWidgets.QRadioButton(self.groupBox)
        self.UsersExp.setGeometry(QtCore.QRect(10, 40, 141, 26))
        self.UsersExp.setChecked(True)
        self.UsersExp.setObjectName("UsersExp")
        self.LocalExp = QtWidgets.QRadioButton(self.groupBox)
        self.LocalExp.setGeometry(QtCore.QRect(10, 70, 141, 26))
        self.LocalExp.setObjectName("LocalExp")
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
        self.groupBox.setTitle(_translate("Dialog", "Experiment Type"))
        self.UsersExp.setText(_translate("Dialog", "Users Experiment"))
        self.LocalExp.setText(_translate("Dialog", "Local Experiment"))

