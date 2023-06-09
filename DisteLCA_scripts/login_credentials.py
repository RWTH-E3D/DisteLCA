from __future__ import annotations
from PySide6.QtWidgets import QDialog, QFormLayout
from PySide6 import QtWidgets
from DisteLCA.helpers import save_component_json, login
import sys


def create_login_gui():
    """
    A grafical user interface (GUI) is displayed using the python package PySide2, where the user has ti eneter a
    username and password for an eLCA account.
    """
    login_credentials = {}

    class Form(QDialog):

        def __init__(self, parent=None):
            super(Form, self).__init__(parent)

            self.password = None
            self.user_name = None
            self.setWindowTitle("DisteLCA")
            layout = QFormLayout()
            self.form_data = []
            self.create_form(layout)

            self.second_button = QtWidgets.QPushButton("Save login credentials")
            layout.addRow(self.second_button)
            self.second_button.clicked.connect(self.press_it_done)
            self.setLayout(layout)

        def create_form(self, layout):

            label_1 = QtWidgets.QLabel("Login credentials for eLCA Bauteileditor https://www.bauteileditor.de/")
            layout.addRow(label_1)
            self.user_name = QtWidgets.QLineEdit(self)
            self.password = QtWidgets.QLineEdit(self)

            layout.addRow("User name:", self.user_name)
            layout.addRow("Password:", self.password)

            self.form_data.append(self.user_name)
            self.form_data.append(self.password)

            self.setLayout(layout)
            return self.form_data

        def press_it_done(self):
            if self.read_values() == 'successful':
                alert = QtWidgets.QMessageBox()
                alert.setWindowTitle("DisteLCA")
                alert.setText(f'You have indicated the following login credentials: {login_credentials}')
                alert.exec_()
                self.close()
            else:
                pass

        def read_values(self):
            login_credentials.update({
                'User name': self.user_name.text(),
                'Password': self.password.text()})
            save_component_json(login_credentials, "login_credentials")
            try:
                login()
                return 'successful'
            except ValueError:
                alert = QtWidgets.QMessageBox()
                alert.setWindowTitle("DisteLCA")
                alert.setText(f'Login unsuccessful! Please provide new login credentials!')
                alert.exec_()
                return 'unsuccessful'

    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    form = Form()
    form.show()
    app.exec_()

    print('The information given on the login credentials has been saved!')
