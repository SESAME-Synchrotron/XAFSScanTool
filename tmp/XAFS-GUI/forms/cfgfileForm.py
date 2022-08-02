# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cfgfile.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CfgFileLocation(object):
    def setupUi(self, CfgFileLocation):
        CfgFileLocation.setObjectName("CfgFileLocation")
        CfgFileLocation.resize(532, 178)
        self.buttonBox = QtWidgets.QDialogButtonBox(CfgFileLocation)
        self.buttonBox.setGeometry(QtCore.QRect(29, 120, 461, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Browse = QtWidgets.QToolButton(CfgFileLocation)
        self.Browse.setGeometry(QtCore.QRect(460, 50, 28, 27))
        self.Browse.setObjectName("Browse")
        self.filePath = QtWidgets.QLineEdit(CfgFileLocation)
        self.filePath.setGeometry(QtCore.QRect(110, 50, 341, 28))
        self.filePath.setObjectName("filePath")
        self.label = QtWidgets.QLabel(CfgFileLocation)
        self.label.setGeometry(QtCore.QRect(10, 50, 81, 20))
        self.label.setObjectName("label")

        self.retranslateUi(CfgFileLocation)
        self.buttonBox.accepted.connect(CfgFileLocation.accept)
        self.buttonBox.rejected.connect(CfgFileLocation.reject)
        QtCore.QMetaObject.connectSlotsByName(CfgFileLocation)

    def retranslateUi(self, CfgFileLocation):
        _translate = QtCore.QCoreApplication.translate
        CfgFileLocation.setWindowTitle(_translate("CfgFileLocation", "Browse .cfg file"))
        self.Browse.setText(_translate("CfgFileLocation", "..."))
        self.label.setText(_translate("CfgFileLocation", "cfg file path"))
