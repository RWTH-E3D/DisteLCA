from __future__ import annotations
from PySide6.QtWidgets import QDialog, QFormLayout
from PySide6 import QtWidgets
from DisteLCA.helpers import load_component_json, save_component_json
import sys


def create_district_gui():
    """
    Load in the templates read out from the eLCA account. A GUI is displayed, where a user can enter information on
    an archetype of the district. For each distric a user has to specify
    - the number of buildings of that archetype,
    - the net and gross floor areas,
    - the final energy demands for heating, hot water, and lighting,
    - the areas of
      all building components included in the analysis,
    - the corresponding eLCA component templates to be selected
      from drop-down menus,
    - the energy source and
    - the building age class.
    The user input is saved in a JSON file.
    """
    templates: list[dict] = load_component_json("templates")
    # JSON file on eLCA energy sources
    energy_sources: dict[str, str] = load_component_json("energy_sources", "buildings_base_data")
    # txt file on building age classes
    construction_age_classes = open("buildings_base_data/construction_age_classes.txt", "r")
    age_classes = construction_age_classes.read()
    age_classes_list = age_classes.replace('\n', '').split(",")
    construction_age_classes.close()
    archetypes = []

    class Form(QDialog):

        def __init__(self, parent=None):
            super(Form, self).__init__(parent)
            self.setWindowTitle("DisteLCA")
            layout = QFormLayout()
            self.form_data = []
            self.create_form(layout)
            self.comp_boxes = []
            cost_groups = {"330": "exterior walls", "334": "windows", "360": "roofs", "320": "foundation",
                           "340": "interior walls", "350": "ceilings", "420": "heating supply system"}
            for cost_group, component_name in cost_groups.items():
                self.create_component_combo_box(layout, cost_group, component_name)
            self.create_energy_carrier_combo_box(layout, energy_sources)
            self.create_age_class_combo_box(layout, age_classes_list)

            self.first_button = QtWidgets.QPushButton("Add another archetype")
            layout.addRow(self.first_button)
            self.first_button.clicked.connect(self.press_it_next)
            self.second_button = QtWidgets.QPushButton("Do not add any more archetypes and show district data")
            layout.addRow(self.second_button)
            self.second_button.clicked.connect(self.press_it_done)
            self.setLayout(layout)

        def create_form(self, layout):

            label_1 = QtWidgets.QLabel("Please add information on one building archetype of the district and add more archetypes with the button below")
            label_1.setStyleSheet("font-size: 17pt")
            layout.addRow(label_1)
            self.archetype_name = QtWidgets.QLineEdit(self)
            self.no_quarter = QtWidgets.QLineEdit(self)
            self.gfa = QtWidgets.QLineEdit(self)
            self.nfa = QtWidgets.QLineEdit(self)
            self.final_energy_heat = QtWidgets.QLineEdit(self)
            self.final_energy_water = QtWidgets.QLineEdit(self)
            self.final_energy_lighting = QtWidgets.QLineEdit(self)
            self.quantity_outer_walls = QtWidgets.QLineEdit(self)
            self.quantity_roof = QtWidgets.QLineEdit(self)
            self.quantity_foundation = QtWidgets.QLineEdit(self)
            self.quantity_windows = QtWidgets.QLineEdit(self)
            self.quantity_interior_walls = QtWidgets.QLineEdit(self)
            self.quantity_ceilings = QtWidgets.QLineEdit(self)

            layout.addRow("Archetype name (no spaces & capital letters combined/ no special characters):", self.archetype_name)
            layout.addRow("Number of buildings of the archetype in the neighbourhood (only integer formats):",
                          self.no_quarter)
            # Line: Gross ground space (gfa) according to DIN 276
            layout.addRow("GFA according to DIN 276  (only integer or float formats):", self.gfa)
            # Line: Net ground space (nfa) according to DIN 276
            layout.addRow("NFA according to DIN 276  (only integer or float formats):", self.nfa)
            # Line: Indication of final energy for heating
            layout.addRow("Final energy for heating in kWh/(m²a)  (only integer or float formats):",
                          self.final_energy_heat)
            # Line: Specification of final energy for hot water
            layout.addRow("Final energy for hot water in kWh/(m²a)  (only integer or float formats):",
                          self.final_energy_water)
            layout.addRow("Final energy for lighting in kWh/(m²a)  (only integer or float formats):",
                          self.final_energy_lighting)
            # Line: Specification of the masses for the outer walls
            layout.addRow("Area of the outer walls in m² (only integer or float formats):", self.quantity_outer_walls)
            # Line: Specification of the masses for the windows
            layout.addRow("Area of the roof in m² (only integer or float formats):", self.quantity_roof)
            # Line: Specification of the masses for the windows
            layout.addRow("Floor plate area in m² (only integer or float formats):", self.quantity_foundation)
            # Line: Specification of the masses for the roof
            layout.addRow("Number of windows (only integer formats):", self.quantity_windows)
            layout.addRow("Interior walls area in m² (only integer or float formats):", self.quantity_interior_walls)
            layout.addRow("Ceilings area (only integer or float formats):", self.quantity_ceilings)

            self.form_data.append(self.archetype_name)
            self.form_data.append(self.no_quarter)
            self.form_data.append(self.gfa)
            self.form_data.append(self.nfa)
            self.form_data.append(self.final_energy_heat)
            self.form_data.append(self.final_energy_water)
            self.form_data.append(self.final_energy_lighting)
            self.form_data.append(self.quantity_outer_walls)
            self.form_data.append(self.quantity_roof)
            self.form_data.append(self.quantity_foundation)
            self.form_data.append(self.quantity_windows)
            self.form_data.append(self.quantity_interior_walls)
            self.form_data.append(self.quantity_ceilings)

            self.setLayout(layout)
            return self.form_data

        def create_component_combo_box(self, layout, cost_group, component_name):
            comp_combo_box = QtWidgets.QComboBox(self)
            for template in templates:
                if template['CG_DIN_276'] == cost_group:
                    comp_combo_box.addItem(template['template_name'], template['UUID'])
            self.layout().addWidget(comp_combo_box)
            layout.addRow(f"Selection {component_name}", comp_combo_box)
            self.comp_boxes.append(comp_combo_box)
            self.setLayout(layout)

        def create_energy_carrier_combo_box(self, layout, energy_sources):
            # Create a Combo box for energy sources
            self.energy_carrier_combo_box = QtWidgets.QComboBox(self)
            for key, value in energy_sources.items():
                # Add the name (key) as currentText parameter of combo box and ID (value) as currentData parameter
                self.energy_carrier_combo_box.addItem(key, value)
                # Create a widget from the combo box
            self.layout().addWidget(self.energy_carrier_combo_box)
            # Line: Set energy carrier combo box and give information on what to choose in this selection box
            layout.addRow("Selection of energy source (for module B6)", self.energy_carrier_combo_box)
            self.setLayout(layout)

        def create_age_class_combo_box(self, layout, age_classes):
            # Create a Combo box for building age class
            self.building_age_combo_box = QtWidgets.QComboBox(self)
            # Add the list of building age classes to the combo box
            self.building_age_combo_box.addItems(age_classes)
            # Create a widget from the combo box
            self.layout().addWidget(self.building_age_combo_box)
            # Line: Set buidling age class combo box and give information on what to choose in this selection box
            layout.addRow("Selection building age class", self.building_age_combo_box)
            self.setLayout(layout)

        def press_it_next(self):
            if self.read_values() == 'Right formats':
                self.clear_values(self.form_data)
            else:
                pass

        def press_it_done(self):
            #self.read_values()
            if self.read_values() == 'Right formats':
                alert = QtWidgets.QMessageBox()
                alert.setWindowTitle("DisteLCA")
                alert.setText(f'You have defined the following building archetypes: {archetypes}')
                save_component_json(archetypes, "archetypes")
                alert.exec_()
                self.close()
            else:
                pass


        def clear_values(self, data):
            for line in data:
                line.clear()

        def read_values(self):
            try:
                archetypes.append({
                    'archetype name': self.archetype_name.text().rstrip(),
                    'occurrence in the quarter': int(self.no_quarter.text()),
                    'GFA in m²': float(self.gfa.text()),
                    'NFA in m²': float(self.nfa.text()),
                    'final energy heating in kWh/m²a': float(self.final_energy_heat.text()),
                    'final energy hot water in kWh/m²a': float(self.final_energy_water.text()),
                    'final energy lighting in kWh/m²a': float(self.final_energy_lighting.text()),
                    'exterior walls area in m²': float(self.quantity_outer_walls.text()),
                    'roof area in m²': float(self.quantity_roof.text()),
                    'foundation area in m²': float(self.quantity_foundation.text()),
                    'number of windows': int(self.quantity_windows.text()),
                    'interior walls area in m²': float(self.quantity_interior_walls.text()),
                    'ceilings area in m²': float(self.quantity_ceilings.text()),
                    'number of heating supply systems': 1,
                    'energy carrier template': self.energy_carrier_combo_box.currentText(),
                    'energy carrier ID': self.energy_carrier_combo_box.currentData(),
                    'exterior walls template': self.comp_boxes[0].currentText(),
                    'window template': self.comp_boxes[1].currentText(),
                    'roof template': self.comp_boxes[2].currentText(),
                    'foundation template': self.comp_boxes[3].currentText(),
                    'interior walls template': self.comp_boxes[4].currentText(),
                    'ceilings template': self.comp_boxes[5].currentText(),
                    'heat supply system template': self.comp_boxes[6].currentText(),
                    'exterior walls ID': self.comp_boxes[0].currentData(),
                    'window ID': self.comp_boxes[1].currentData(),
                    'roof ID': self.comp_boxes[2].currentData(),
                    'foundation ID': self.comp_boxes[3].currentData(),
                    'interior walls ID': self.comp_boxes[4].currentData(),
                    'ceilings ID': self.comp_boxes[5].currentData(),
                    'heat supply system ID': self.comp_boxes[6].currentData(),
                    'building age class': self.building_age_combo_box.currentText()
                })
                return 'Right formats'
            except ValueError:
                alert = QtWidgets.QMessageBox()
                alert.setWindowTitle("DisteLCA")
                alert.setText(f'An error occured! Please check the formats of the data on the archetype!')
                alert.exec_()
                return 'Error'


    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    form = Form()
    form.show()
    app.exec_()
    print('The information given on the archetypes of the quarter has been saved!')
