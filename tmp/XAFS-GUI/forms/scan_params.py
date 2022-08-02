# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scan_params.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(434, 253)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 411, 231))
        self.groupBox.setObjectName("groupBox")
        self.setNumofIterv = QtWidgets.QLineEdit(self.groupBox)
        self.setNumofIterv.setGeometry(QtCore.QRect(170, 30, 110, 20))
        self.setNumofIterv.setObjectName("setNumofIterv")
        self.setNumofSamples = QtWidgets.QLineEdit(self.groupBox)
        self.setNumofSamples.setGeometry(QtCore.QRect(170, 60, 110, 20))
        self.setNumofSamples.setObjectName("setNumofSamples")
        self.label_33 = QtWidgets.QLabel(self.groupBox)
        self.label_33.setGeometry(QtCore.QRect(20, 60, 131, 20))
        self.label_33.setObjectName("label_33")
        self.label_34 = QtWidgets.QLabel(self.groupBox)
        self.label_34.setGeometry(QtCore.QRect(20, 90, 151, 20))
        self.label_34.setObjectName("label_34")
        self.label_36 = QtWidgets.QLabel(self.groupBox)
        self.label_36.setGeometry(QtCore.QRect(20, 30, 131, 20))
        self.label_36.setObjectName("label_36")
        self.setNumofExafsScans = QtWidgets.QLineEdit(self.groupBox)
        self.setNumofExafsScans.setGeometry(QtCore.QRect(170, 90, 110, 20))
        self.setNumofExafsScans.setObjectName("setNumofExafsScans")
        self.editIntrv = QtWidgets.QPushButton(self.groupBox)
        self.editIntrv.setGeometry(QtCore.QRect(290, 30, 110, 20))
        self.editIntrv.setObjectName("editIntrv")
        self.editSample = QtWidgets.QPushButton(self.groupBox)
        self.editSample.setGeometry(QtCore.QRect(290, 60, 110, 20))
        self.editSample.setObjectName("editSample")
        self.label_35 = QtWidgets.QLabel(self.groupBox)
        self.label_35.setGeometry(QtCore.QRect(20, 150, 151, 20))
        self.label_35.setObjectName("label_35")
        self.setDataFileName = QtWidgets.QLineEdit(self.groupBox)
        self.setDataFileName.setGeometry(QtCore.QRect(170, 150, 220, 20))
        self.setDataFileName.setObjectName("setDataFileName")
        self.StartScan = QtWidgets.QPushButton(self.groupBox)
        self.StartScan.setGeometry(QtCore.QRect(170, 180, 110, 20))
        self.StartScan.setObjectName("StartScan")
        self.label_37 = QtWidgets.QLabel(self.groupBox)
        self.label_37.setGeometry(QtCore.QRect(20, 120, 131, 20))
        self.label_37.setObjectName("label_37")
        self.configureDetectors = QtWidgets.QPushButton(self.groupBox)
        self.configureDetectors.setGeometry(QtCore.QRect(290, 120, 110, 20))
        self.configureDetectors.setObjectName("configureDetectors")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "Experiment setup parameters"))
        self.label_33.setText(_translate("Dialog", "number of samples"))
        self.label_34.setText(_translate("Dialog", "number of exafs scans"))
        self.label_36.setText(_translate("Dialog", "number of intervals"))
        self.editIntrv.setText(_translate("Dialog", "edit interval"))
        self.editSample.setText(_translate("Dialog", "edit sample"))
        self.label_35.setText(_translate("Dialog", "data file name"))
        self.StartScan.setText(_translate("Dialog", "start scan"))
        self.label_37.setText(_translate("Dialog", "Detectors"))
        self.configureDetectors.setText(_translate("Dialog", "configure"))

