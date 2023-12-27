import re
import sys

# from pymongo import MongoClient, errors
from pymilvus import connections, db, exceptions
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication
from pymongo import MongoClient, errors
import requests
from requests.exceptions import ConnectionError

from src.ai_module import AI
# from src.chartWidgetFunctions import ChartWidgetFunctions
# from src.registerFunctions import RegisterFunctions
from src.setupWidgetFunctions import SetupWidgetFunction
from src.livestreamFunctions import LiveStreamFunctions
# from src.settingWidgetFunction import SettingWidgetFunction
from src.violation import ViolationFunction
from ui.ui_functions import UIFunctions
from ui.ui_mainwindow import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentWidget(self.ui.setupWidget)
        
        self.ui.checkButton.clicked.connect(self.simulateEnterKeyPress)
        self.ui.comboBoxServerIP.textActivated.connect(self.recv_text)
        self.ui.exitButton.clicked.connect(self.exit_button_clicked)
        
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        
        self.ui.retranslateUi(self)
        self.showMaximized()

    @QtCore.pyqtSlot(str)
    def recv_text(self, text):
        try:
            # conn = connections.connect(host=f'{text}', port=19530)
            # self.database = db.list_database()
            # print(self.database)
            client = MongoClient(f"mongodb://10.37.239.102:9999", serverSelectionTimeoutMS=5000)
            self.db = client["vehicles_db"]
            self.db.list_collection_names()

            ip_address = self.ui.comboBoxServerIP.currentText()

            if ip_address == "":
                QtWidgets.QMessageBox.critical(self, "ERROR", "Chưa nhập IP Server!")
                return

            ip_pattern = r"^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})$"

            if not re.match(ip_pattern, ip_address):
                QtWidgets.QMessageBox.critical(
                    self, "ERROR", "Địa chỉ IP nhập vào không hợp lệ!"
                )
                return

            try:
                recog_server = f"http://{ip_address}:8090/ping"
                requests.get(recog_server)
            except ConnectionError:
                QtWidgets.QMessageBox.critical(
                    self, "ERROR", "Kết nối server thất bại!"
                )
                return

            QtWidgets.QMessageBox.information(self, "INFO", "Kết nối database thành công!")
            self.ui.checkButton.setEnabled(False)

            self.ui_functions = UIFunctions(self.ui)
            self.setup_functions = SetupWidgetFunction(self)
            self.livestream_funcs = LiveStreamFunctions(self)
            self.ai_functions = AI(self)
            # self.setting_functions = SettingWidgetFunction(self)
            # self.chart_functions = ChartWidgetFunctions(self)
            self.violation_functions = ViolationFunction(self)

            # Navigation buttons
            self.ui.btnMenu.toggled.connect(self.ui_functions.toggleMenu)
            self.ui.btnRegisterUserPage.toggled.connect(self.ui_functions.toggleRegister)
            self.ui.btnSetupPage.toggled.connect(self.ui_functions.toggleSetup)
            self.ui.btnLiveStreamPage.toggled.connect(self.ui_functions.toggleLiveStream)
            # self.ui.btnChartPage.toggled.connect(self.ui_functions.toggleChart)
            self.ui.btnViolationPage.toggled.connect(self.ui_functions.toggleViolation)
            # self.ui.btnSettingPage.toggled.connect(self.ui_functions.toggleSetting)

            # Emit data from setup page to livestream page
            self.setup_functions.send_table_data.connect(self.livestream_funcs.recv_table_data)
            self.setup_functions.send_remove_cam_signal.connect(self.livestream_funcs.recv_remove_cam_signal)
            # self.setup_functions.send_cam_names.connect(self.setting_functions.receive_cam_names)

            # Emit data from livestream page to setup page
            self.livestream_funcs.send_camera_update_status.connect(self.setup_functions.recv_camera_status)
            self.ui.startLiveButton.clicked.connect(self.livestream_funcs.on_playButtonClicked)
            self.ui.stopLiveButton.clicked.connect(self.livestream_funcs.on_stopButtonClicked)

            # Buttons in setup page
            self.ui.btnAddRow.clicked.connect(self.setup_functions.on_addDataClicked)
            # self.ui.btnAddRow.clicked.connect(self.setting_functions.on_addDataClicked)
            self.ui.btnDelRow.clicked.connect(self.setup_functions.on_deleteDataClicked)

            self.ui.btnOpenFile.clicked.connect(self.setup_functions.on_openFile)
            self.ui.btnOpenFile.clicked.connect(self.setup_functions.on_initButtonClicked)
            self.ui.btnExportFile.clicked.connect(self.setup_functions.on_writeExcelClicked)
            self.ui.btnSelectROI.clicked.connect(self.setup_functions.on_selectROI)
            self.ui.btnLive.clicked.connect(self.setup_functions.on_LiveStreamClicked)

            # Change grid layout button in livestream page
            self.ui.btnCompactLS.toggled.connect(self.livestream_funcs.toggleCompactMode)

            # Search field in setup page
            # self.ui.tableFieldCB.addItems(self.setup_functions.setupModel.dataframe.columns)
            self.ui.tableFieldCB.currentIndexChanged.connect(self.setup_functions.filterColumnSearch)
            self.ui.tableSearch.textChanged.connect(self.setup_functions.update_search)
            self.ui.labelLoading.setVisible(False)

            # self.ui.btnFilter.clicked.connect(self.chart_functions.on_FilterClicked)
            self.ui.btnFilterVio.clicked.connect(self.violation_functions.on_FilterClicked)
            self.ui.tableFieldCB_Vio.addItems(self.violation_functions.get_columns())
            self.ui.tableFieldCB_Vio.currentIndexChanged.connect(self.violation_functions.filterColumnSearch)
            self.ui.tableSearch_Vio.textChanged.connect(self.violation_functions.update_search)
            self.violation_functions.send_display_image_error.connect(self.recv_display_image_error)
            
        except errors.ServerSelectionTimeoutError:
            QtWidgets.QMessageBox.critical(self, "ERROR", "Kết nối tới server thất bại!")
        

    @QtCore.pyqtSlot(str)
    def recv_display_image_error(self, error: str):
        QtWidgets.QMessageBox.critical(self, "ERROR", f"{error}")

    def simulateEnterKeyPress(self):
        # Set focus to the text box
        self.ui.comboBoxServerIP.setFocus()        
        # Create a key event to simulate pressing Enter
        enter_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Enter, Qt.NoModifier)

        # Send the Enter key event to the focused widget (the text box)
        QApplication.sendEvent(self.ui.comboBoxServerIP, enter_event)

    def exit_button_clicked(self):
        ret = QtWidgets.QMessageBox.information(self,
            "Thông báo",
            "Bạn có muốn thoát chương trình?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if ret == QtWidgets.QMessageBox.Yes:
            if hasattr(self, 'livestream_funcs') and self.livestream_funcs is not None:
                self.livestream_funcs.remove_all_cameras()
                self.close()
            else:
                self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app_icon = QtGui.QIcon(":/App_Icon/icons/app.ico")
    app.setWindowIcon(app_icon)
    
    window = MainWindow()
    window.setWindowTitle("LANCS")
    window.show()
    
    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window...')