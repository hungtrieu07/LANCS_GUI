# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/selectROIdialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SelectROIDialog(object):
    def setupUi(self, SelectROIDialog):
        SelectROIDialog.setObjectName("SelectROIDialog")
        SelectROIDialog.resize(936, 576)
        SelectROIDialog.setStyleSheet("QFrame, QDialog {\n"
"background-color: white;\n"
"}\n"
"\n"
"#btnROIFrame {\n"
"border-top: 1px solid #b0b0b0;\n"
"}\n"
"\n"
"QLabel, #roiTitlelbl {\n"
"color: black;\n"
"font: 20px;\n"
"font-weight: bold;\n"
"}\n"
"\n"
"/* Style PushButton */\n"
"\n"
"QPushButton {\n"
"border: none;\n"
"border-bottom: 1px solid #b0b0b0;\n"
"border-bottom-left-radius: 10px;\n"
"border-bottom-right-radius: 10px;\n"
"background-color: #FFFFFF;\n"
"color: #000000;\n"
"font-weight: bold;\n"
"font: 15px;\n"
"}\n"
"\n"
"QPushButton::hover {\n"
"color: #2f9aff;\n"
"border-bottom: 4px solid #2f9aff;\n"
"}\n"
"\n"
"QPushButton::pressed {\n"
"background-color: 2f9aff;\n"
"border-radius: 10px;\n"
"border-bottom: 2px solid #2f9aff;\n"
"background-color: #c6c6c6\n"
"}\n"
"\n"
"#btnFinish {\n"
"border: none;\n"
"border-bottom-left-radius: none;\n"
"border-top-left-radius: 10px;\n"
"border-top: 2px solid #b0b0b0;\n"
"border-left: 2px solid #b0b0b0;\n"
"}\n"
"\n"
"#btnFinish::hover {\n"
"border-top: 4px solid #ff373a;\n"
"border-left: 4px solid #ff373a;\n"
"}\n"
"\n"
"#btnFinish::pressed {\n"
"border-top: 2px solid #ff373a;\n"
"border-left: 2px solid #ff373a;\n"
"}\n"
"\n"
"/* Style TableView and Header */\n"
"\n"
"QTableView {\n"
"background-color: #FFFFFF;\n"
"color: black;\n"
"border: 1px solid  #b0b0b0;\n"
"border-radius: 10px;\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"background-color:  #d8f8ff;\n"
"color: black;\n"
"border: 1px solid  #b0b0b0;\n"
"}\n"
"\n"
"/* Style stacked widget */\n"
"#stackROILabel {\n"
"border: 1px #b0b0b0;\n"
"}")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(SelectROIDialog)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.roiTitlelbl = QtWidgets.QLabel(SelectROIDialog)
        self.roiTitlelbl.setAlignment(QtCore.Qt.AlignCenter)
        self.roiTitlelbl.setObjectName("roiTitlelbl")
        self.verticalLayout_2.addWidget(self.roiTitlelbl)
        self.bodyFrame = QtWidgets.QFrame(SelectROIDialog)
        self.bodyFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.bodyFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bodyFrame.setObjectName("bodyFrame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.bodyFrame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.leftFrame = QtWidgets.QFrame(self.bodyFrame)
        self.leftFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.leftFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.leftFrame.setObjectName("leftFrame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.leftFrame)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName("verticalLayout")
        self.stackROILabel = QtWidgets.QStackedWidget(self.leftFrame)
        self.stackROILabel.setObjectName("stackROILabel")
        self.verticalLayout.addWidget(self.stackROILabel)
        self.btnROIFrame = QtWidgets.QFrame(self.leftFrame)
        self.btnROIFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.btnROIFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.btnROIFrame.setObjectName("btnROIFrame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.btnROIFrame)
        self.horizontalLayout.setContentsMargins(0, 4, 0, 4)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnBack = QtWidgets.QPushButton(self.btnROIFrame)
        self.btnBack.setMinimumSize(QtCore.QSize(40, 40))
        self.btnBack.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnBack.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/LeftArrow/icons/arrow-left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnBack.setIcon(icon)
        self.btnBack.setIconSize(QtCore.QSize(26, 26))
        self.btnBack.setObjectName("btnBack")
        self.horizontalLayout.addWidget(self.btnBack, 0, QtCore.Qt.AlignLeft)
        self.btnClear = QtWidgets.QPushButton(self.btnROIFrame)
        self.btnClear.setMinimumSize(QtCore.QSize(40, 40))
        self.btnClear.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnClear.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Clean/icons/clean.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnClear.setIcon(icon1)
        self.btnClear.setIconSize(QtCore.QSize(26, 26))
        self.btnClear.setObjectName("btnClear")
        self.horizontalLayout.addWidget(self.btnClear, 0, QtCore.Qt.AlignHCenter)
        self.btnNext = QtWidgets.QPushButton(self.btnROIFrame)
        self.btnNext.setMinimumSize(QtCore.QSize(40, 40))
        self.btnNext.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnNext.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/RightArrow/icons/arrow-right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnNext.setIcon(icon2)
        self.btnNext.setIconSize(QtCore.QSize(26, 26))
        self.btnNext.setObjectName("btnNext")
        self.horizontalLayout.addWidget(self.btnNext, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addWidget(self.btnROIFrame)
        self.horizontalLayout_2.addWidget(self.leftFrame)
        self.tableView = QtWidgets.QTableView(self.bodyFrame)
        self.tableView.setMinimumSize(QtCore.QSize(300, 0))
        self.tableView.setMaximumSize(QtCore.QSize(300, 16777215))
        self.tableView.setGridStyle(QtCore.Qt.SolidLine)
        self.tableView.setWordWrap(False)
        self.tableView.setObjectName("tableView")
        self.horizontalLayout_2.addWidget(self.tableView)
        self.verticalLayout_2.addWidget(self.bodyFrame)
        self.btnFinish = QtWidgets.QPushButton(SelectROIDialog)
        self.btnFinish.setMinimumSize(QtCore.QSize(40, 40))
        self.btnFinish.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnFinish.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/Escape/icons/escape.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnFinish.setIcon(icon3)
        self.btnFinish.setIconSize(QtCore.QSize(26, 26))
        self.btnFinish.setObjectName("btnFinish")
        self.verticalLayout_2.addWidget(self.btnFinish, 0, QtCore.Qt.AlignRight)

        self.retranslateUi(SelectROIDialog)
        QtCore.QMetaObject.connectSlotsByName(SelectROIDialog)

    def retranslateUi(self, SelectROIDialog):
        _translate = QtCore.QCoreApplication.translate
        SelectROIDialog.setWindowTitle(_translate("SelectROIDialog", "Dialog"))
        self.roiTitlelbl.setText(_translate("SelectROIDialog", "SELECT ROI"))
import resources_rc