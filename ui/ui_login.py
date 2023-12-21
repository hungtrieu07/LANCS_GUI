# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\designer\login.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LoginForm(object):
    def setupUi(self, LoginForm):
        LoginForm.setObjectName("LoginForm")
        LoginForm.setWindowModality(QtCore.Qt.NonModal)
        LoginForm.resize(513, 490)
        self.programName = QtWidgets.QLabel(LoginForm)
        self.programName.setGeometry(QtCore.QRect(9, 6, 495, 50))
        self.programName.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.programName.setFont(font)
        self.programName.setAlignment(QtCore.Qt.AlignCenter)
        self.programName.setObjectName("programName")
        self.loginName = QtWidgets.QLabel(LoginForm)
        self.loginName.setGeometry(QtCore.QRect(9, 62, 495, 25))
        self.loginName.setMinimumSize(QtCore.QSize(0, 0))
        self.loginName.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.loginName.setFont(font)
        self.loginName.setAlignment(QtCore.Qt.AlignCenter)
        self.loginName.setObjectName("loginName")
        self.layoutWidget = QtWidgets.QWidget(LoginForm)
        self.layoutWidget.setGeometry(QtCore.QRect(96, 450, 331, 41))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.register_button = QtWidgets.QPushButton(self.layoutWidget)
        self.register_button.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.register_button.setObjectName("register_button")
        self.horizontalLayout_2.addWidget(self.register_button)
        self.login_button = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.login_button.setFont(font)
        self.login_button.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.login_button.setAutoDefault(True)
        self.login_button.setDefault(True)
        self.login_button.setObjectName("login_button")
        self.horizontalLayout_2.addWidget(self.login_button)
        self.layoutWidget1 = QtWidgets.QWidget(LoginForm)
        self.layoutWidget1.setGeometry(QtCore.QRect(14, 120, 491, 331))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget1)
        self.gridLayout.setContentsMargins(0, 0, 0, 6)
        self.gridLayout.setObjectName("gridLayout")
        self.serverIPLabel = QtWidgets.QLabel(self.layoutWidget1)
        self.serverIPLabel.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.serverIPLabel.setFont(font)
        self.serverIPLabel.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.serverIPLabel.setObjectName("serverIPLabel")
        self.gridLayout.addWidget(self.serverIPLabel, 0, 0, 1, 1)
        self.serverIPEdit = QtWidgets.QLineEdit(self.layoutWidget1)
        self.serverIPEdit.setMinimumSize(QtCore.QSize(0, 0))
        self.serverIPEdit.setMaximumSize(QtCore.QSize(453, 16777215))
        self.serverIPEdit.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.serverIPEdit.setObjectName("serverIPEdit")
        self.gridLayout.addWidget(self.serverIPEdit, 1, 0, 1, 1)
        self.usernameLabel = QtWidgets.QLabel(self.layoutWidget1)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.usernameLabel.setFont(font)
        self.usernameLabel.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.usernameLabel.setObjectName("usernameLabel")
        self.gridLayout.addWidget(self.usernameLabel, 2, 0, 1, 1)
        self.username = QtWidgets.QLineEdit(self.layoutWidget1)
        self.username.setMaximumSize(QtCore.QSize(453, 16777215))
        self.username.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.username.setObjectName("username")
        self.gridLayout.addWidget(self.username, 3, 0, 1, 1)
        self.passwordLabel = QtWidgets.QLabel(self.layoutWidget1)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.passwordLabel.setFont(font)
        self.passwordLabel.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.passwordLabel.setObjectName("passwordLabel")
        self.gridLayout.addWidget(self.passwordLabel, 4, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.password = QtWidgets.QLineEdit(self.layoutWidget1)
        self.password.setStyleSheet("font: 12pt \"Segoe UI\";")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.horizontalLayout.addWidget(self.password)
        self.showHidePasswordButton = QtWidgets.QPushButton(self.layoutWidget1)
        self.showHidePasswordButton.setMaximumSize(QtCore.QSize(16777215, 27))
        self.showHidePasswordButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Password/icons/view.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap(":/Password/icons/hide.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.showHidePasswordButton.setIcon(icon)
        self.showHidePasswordButton.setObjectName("showHidePasswordButton")
        self.horizontalLayout.addWidget(self.showHidePasswordButton)
        self.gridLayout.addLayout(self.horizontalLayout, 5, 0, 1, 1)

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)

    def retranslateUi(self, LoginForm):
        _translate = QtCore.QCoreApplication.translate
        LoginForm.setWindowTitle(_translate("LoginForm", "Form"))
        self.programName.setText(_translate("LoginForm", "VEHICLE DETECTION SYSTEM"))
        self.loginName.setText(_translate("LoginForm", "ĐĂNG NHẬP"))
        self.register_button.setText(_translate("LoginForm", "Đăng ký"))
        self.login_button.setText(_translate("LoginForm", "Đăng nhập"))
        self.serverIPLabel.setText(_translate("LoginForm", "Địa chỉ IP Server"))
        self.usernameLabel.setText(_translate("LoginForm", "Tên đăng nhập"))
        self.passwordLabel.setText(_translate("LoginForm", "Mật khẩu"))
import resources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    LoginForm = QtWidgets.QWidget()
    ui = Ui_LoginForm()
    ui.setupUi(LoginForm)
    LoginForm.show()
    sys.exit(app.exec_())
