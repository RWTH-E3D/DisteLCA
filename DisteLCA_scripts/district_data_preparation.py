# instead of "from typing import Union": Union[str, int] == str | int
from __future__ import annotations
import os
from pathlib import Path
from DisteLCA.helpers import load_component_json, save_component_json, save_elca_csv, create_district_report_dirs


def prepare_district_data():
    """
    The user input is read in from archetypes.JSON. The data from the JSON file has to be processed to enable project
    creation in eLCA through CSV import. Therefore, for every archetype of the district, a CSV file with the
    necessary components and a JSON file with further semantic data to send to the web server is created.
    """
    # Create report data folders if they don't exist already
    create_district_report_dirs()
    # load the information on the user-defined archetypes from archetypes.json
    archetypes: list[dict] = load_component_json("archetypes")
    for archetype in archetypes:
        # Create sub folder with name of the archetype for each archetype in temp_data
        folder_name = Path('temp_data') / archetype['archetype name']
        os.makedirs(folder_name, exist_ok=True)
        # Create dictionaries with project data for the JSON file
        # This data is required to create a project in eLCA via CSV-Import
        stock_project_data: dict[str, str | int | float] = {
            'projectname': archetype['archetype name'],
            'gross_floor_area': archetype['GFA in m²'],
            'net_floor_area': archetype['NFA in m²'],
            'energy_heating': archetype['final energy heating in kWh/m²a'],
            'energy_water': archetype['final energy hot water in kWh/m²a'],
            'energy_lighting': archetype['final energy lighting in kWh/m²a'],
            'energy_source': archetype['energy carrier ID']
        }

        # Create one dictionary for each row of the CSV file,
        # that will contain the components used in the specific project
        def csv_components(component_name: str, cost_group: int, mass_name: str, unit: str, id_name: str) -> dict[
            str, str | int | float]:
            if archetype[component_name] == "Outside the scope of the study":
                csv_dict = None
            else:
                csv_dict = {'Name': archetype[component_name],
                            'KG DIN 276': cost_group,
                            'Fläche': archetype[mass_name],
                            'Bezugsgröße': unit,
                            'eLCA BT ID': archetype[id_name]
                            }
            return csv_dict

        stock_outer_wall = csv_components('exterior walls template', 330, 'exterior walls area in m²', 'm²',
                                          'exterior walls ID')
        stock_window = csv_components('window template', 334, 'number of windows', 'Stück', 'window ID')
        stock_roof = csv_components('roof template', 360, 'roof area in m²', 'm²', 'roof ID')
        stock_foundation = csv_components('foundation template', 320, 'foundation area in m²', 'm²', 'foundation ID')
        stock_interior_walls = csv_components('interior walls template', 340, 'interior walls area in m²', 'm²',
                                              'interior walls ID')
        stock_ceilings = csv_components('ceilings template', 350, 'ceilings area in m²', 'm²', 'ceilings ID')
        stock_hss = csv_components('heat supply system template', 420, 'number of heating supply systems', 'Stück',
                                   'heat supply system ID')
        # save the csv and json files
        save_elca_csv(
            [stock_outer_wall, stock_window, stock_roof, stock_foundation, stock_interior_walls, stock_ceilings,
             stock_hss],
            archetype['archetype name'],
            folder=folder_name)
        save_component_json(stock_project_data,
                            archetype['archetype name'],
                            folder=folder_name)

    print('Data has been prepared for the projects creation!')
