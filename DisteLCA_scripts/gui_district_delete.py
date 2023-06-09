from __future__ import annotations
import glob
import os
import os.path
import shutil
import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QFormLayout
from DisteLCA.helpers import login, projects_dict


def delete_district_projects():
    """
    The user can choose in a grafical user interface by clicking buttons between the deletion of all data,
    including the eLCA projects and the result files, which is necessary for the restart of DisteLCA, or the deletion
    of only the eLCA projects or no deletion at all.
    """
    class DeleteWindow(QDialog):
        def __init__(self, parent=None):
            super(DeleteWindow, self).__init__(parent)
            self.setWindowTitle("DisteLCA")
            form_layout = QFormLayout()
            self.setLayout(form_layout)
            # Add widgets

            label_1 = QtWidgets.QLabel("Do you want to delete all data of the quarter? This may take a few minutes.")
            form_layout.addRow(label_1)

            self.session = login()
            self.projects = projects_dict(self.session)

            self.first_button = QtWidgets.QPushButton("Delete only the eLCA projects and the temporary data! The "
                                                      "report files must then be deleted manually before the next "
                                                      "execution of the tool.")
            form_layout.addRow(self.first_button)
            self.first_button.clicked.connect(self.press_delete)

            self.second_button = QtWidgets.QPushButton(
                "Delete all data (eLCA projects, temporary files and report files)!")
            form_layout.addRow(self.second_button)
            self.second_button.clicked.connect(self.press_delete_results)

            self.third_button = QtWidgets.QPushButton("Delete nothing!")
            form_layout.addRow(self.third_button)
            self.third_button.clicked.connect(self.press_not_delete)

            # If " Delete temporary files and eLCA projects" is pressed:

        def press_delete(self):

            try:
                # Read project-IDs and create dictionary of project_id as keys and project_name as value
                # Delete all projects
                for (key, value) in self.projects.items():
                    response = self.session.get(
                        "https://www.bauteileditor.de/projects/delete/?confirmed&id={}".format(key))
                    print("Project {} is deleted...".format(value))
                print(f'All projects have been deleted.')
            # If there are no projects in the account, show error message
            except AttributeError:
                print(f'There are no projects in the account that could be deleted')

            # Delete the directories of the archetypes in "temp_data"
            # Create list of all folders and files in "temp_data"
            filelist = glob.glob(os.path.join("temp_data", "*"))
            # Iterate through list
            for f in filelist:
                try:
                    # If it is a directiory it can be deleted through this line
                    shutil.rmtree(f)
                    print(f'{f} has been deleted!')
                # "try" for all files and "except" for all folders
                # If it is not a directory, pass
                except NotADirectoryError:
                    pass
            print("All temporary files have been deleted!")
            # Message Box
            alert1 = QtWidgets.QMessageBox()
            alert1.setWindowTitle("disteLCA")
            alert1.setText(
                'All eLCA projects and temporary files of the quarter have been deleted. The report files '
                'must be deleted manually before the next execution of the tool.')
            alert1.exec_()
            self.close()

        # If "Delete temporary files, eLCA projects and result files" is pressed:
        def press_delete_results(self):
            # Enter all accounts
            try:
                # Delete all projects
                for (key, value) in self.projects.items():
                    response = self.session.get(
                        "https://www.bauteileditor.de/projects/delete/?confirmed&id={}".format(key))
                    print("Project {} is deleted...".format(value))
                print(f'AAll projects have been deleted.')
            # If there are no projects in the account, show error message
            except AttributeError:
                print('There are no projects included that could be deleted.')
            # Delete the directories of the archetypes in "temp_data"
            # Create list of all folders and files in "temp_data"
            filelist = glob.glob(os.path.join("temp_data", "*"))
            # Iterate through list
            for f in filelist:
                try:
                    # If it is a directory it can be deleted through this line
                    shutil.rmtree(f)
                    print(f'{f} has been deleted!')
                # "try" for all files and "except" for all folders
                # If it is not a directory, pass
                except NotADirectoryError:
                    pass
            print("All temporary files have been deleted!")

            # Make lists of files for every directory in district_reports
            lci_files = glob.glob(os.path.join("district_reports\\life_cycle_inventory", "*"))
            lcia_files = glob.glob(os.path.join("district_reports\\life_cycle_impact", "*"))

            # Create list of files for all files in district_reports
            list_of_file_lists = [lci_files, lcia_files]
            # Iterate through all files in the directory district_reports to delete the files
            for directory in list_of_file_lists:
                for file in directory:
                    os.remove(file)
                    print(f"{file} has been deleted!")

            print("All data on the quarter has been deleted!")
            # Message Box
            alert2 = QtWidgets.QMessageBox()
            alert2.setWindowTitle("disteLCA")
            alert2.setText('All data on the quarter has been deleted.')
            alert2.exec_()
            self.close()

        def press_not_delete(self):
            # No deletion of the data
            alert = QtWidgets.QMessageBox()
            alert.setWindowTitle("disteLCA")
            alert.setText('The data is not automatically deleted.')
            alert.exec_()
            self.close()
            print("The data is not automatically deleted.")

    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    main_window = DeleteWindow()
    main_window.show()
    app.exec_()
