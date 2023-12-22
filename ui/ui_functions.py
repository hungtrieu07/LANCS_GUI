from PyQt5 import QtCore, QtGui, QtWidgets

from ui.ui_mainwindow import Ui_MainWindow


class UIFunctions:
    def __init__(self, parent):
        self.ui: Ui_MainWindow = parent
        
    def toggleRegister(self, state: bool):
        if state:
            self.ui.stackedWidget.setCurrentWidget(self.ui.RegisterWidget)
            self.ui.btnSetupPage.setChecked(False)
            self.ui.btnLiveStreamPage.setChecked(False)
            self.ui.btnViolationPage.setChecked(False)

    def toggleSetup(self, state: bool):
        if state:
            self.ui.stackedWidget.setCurrentWidget(self.ui.setupWidget)
            self.ui.btnLiveStreamPage.setChecked(False)
            self.ui.btnRegisterUserPage.setChecked(False)
            self.ui.btnViolationPage.setChecked(False)

    def toggleLiveStream(self, state: bool):
        if state:
            self.ui.stackedWidget.setCurrentWidget(self.ui.livestreamWidget)
            self.ui.btnRegisterUserPage.setChecked(False)
            self.ui.btnSetupPage.setChecked(False)
            self.ui.btnViolationPage.setChecked(False)

    def toggleViolation(self, state: bool):
        if state:
            self.ui.stackedWidget.setCurrentWidget(self.ui.violationWidget)
            self.ui.btnSetupPage.setChecked(False)
            self.ui.btnLiveStreamPage.setChecked(False)
            self.ui.btnRegisterUserPage.setChecked(False)

    def toggleMenu(self, state: bool):
        if not state:
            self.animation1 = QtCore.QPropertyAnimation(self.ui.menuBarFrame, b"maximumWidth")
            self.animation1.setDuration(350)
            self.animation1.setStartValue(150)
            self.animation1.setEndValue(0)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()
            
            self.animation2 = QtCore.QPropertyAnimation(self.ui.menuBarFrame, b"minimumWidth")
            self.animation2.setDuration(350)
            self.animation2.setStartValue(150)
            self.animation2.setEndValue(0)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()
        
        else:
            self.animation1 = QtCore.QPropertyAnimation(self.ui.menuBarFrame, b"maximumWidth")
            self.animation1.setDuration(350)
            self.animation1.setStartValue(0)
            self.animation1.setEndValue(150)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()
            
            self.animation2 = QtCore.QPropertyAnimation(self.ui.menuBarFrame, b"minimumWidth")
            self.animation2.setDuration(350)
            self.animation2.setStartValue(0)
            self.animation2.setEndValue(150)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()
            
    def onExitButtonClicked(self, event):
        reply = QtWidgets.QMessageBox.question(self, "Thông báo", "Bạn có muốn thoát khỏi chương trình không?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
        

