import re
import pandas as pd
from DisteLCA.helpers import load_component_json, login, create_get_soup, create_post_soup, projects_dict, create_table, \
    create_district_report_dirs


def compile_district_lci():
    """
    Enter the specified eLCA account and the projects just created. Read out the evaluation data on the life cycle
    inventory of the projects. Compile them into tables and upscale data to the district level by multiplying the
    single building results with the number of buildings of that archetype in the district. Save all results in CSV
    files. DisteLCA's life cycle inventory includes an overview of the building operation, a list of all materials
    and corresponding masses, and a summary of the user input data.
    """
    # Create report data folders if they don't exist already
    create_district_report_dirs()
    # Load information from user input
    archetypes: list[dict] = load_component_json("archetypes")
    # Create dictionary of all final energy demands and fill it later
    operation_frame = pd.DataFrame(columns=['project', 'heating and hot water system', 'energy for heating and hot '
                                                                                       'water in kWh/m²a',
                                            'electricity', 'energy for electricity in kWh/m²a', 'energy for heating '
                                                                                                'and hot water on '
                                                                                                'quarter scale in '
                                                                                                'kWh/a', 'energy for '
                                                                                                         'electricity '
                                                                                                         'on quarter '
                                                                                                         'scale in '
                                                                                                         'kWh/a'])
    session = login()
    # Make dictionary of projects
    projects = projects_dict(session)
    project_names = list(projects.values())
    # Dictionary for material masses for each project of the archetype
    masses_frames_dict = {}
    for project_id, project_name in projects.items():
        # No spaces name is needed for file saving
        no_spaces_name = project_name.replace(' ', '')
        # Find number of buildings of that archetype in quarter and ngs
        no_in_quarter = (next((item for item in archetypes if item['archetype name'] == project_name), None))[
            'occurrence in the quarter']
        net_ground_space = (next((item for item in archetypes if item['archetype name'] == project_name), None))[
            'NFA in m²']
        # Update session header
        response_project_overview = session.get("https://www.bauteileditor.de/projects/{}/".format(project_id))
        # Read final energy demand for each project
        operation_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-report-assets/operation/',
                                         'Elca\\View\\Report\\ElcaReportAssetsView')
        try:
            heating_supplier = operation_soup.find('ul', attrs={'class': 'category final-energy'}).find_all('li')[
                0].find('h2').text
            heating_energy = operation_soup.find('ul', attrs={'class': 'category final-energy'}).find_all('li')[0].find(
                'dd').text
            electricity_name = operation_soup.find('ul', attrs={'class': 'category final-energy'}).find_all('li')[
                1].find('h2').text
            electricity_energy = operation_soup.find('ul', attrs={'class': 'category final-energy'}).find_all('li')[
                1].find('dd').text
            heating_float = float(re.search(r"[-+]?(?:\d*\.\d+|\d+)", heating_energy.replace(',', '.')).group(0))
            electricity_float = float(
                re.search(r"[-+]?(?:\d*\.\d+|\d+)", electricity_energy.replace(',', '.')).group(0))
            quarter_heating_energy = round(heating_float * no_in_quarter * net_ground_space, 2)
            quarter_electricity = round(electricity_float * no_in_quarter * net_ground_space, 2)

        except (AttributeError, IndexError) as e:
            heating_supplier = None
            heating_float = None
            electricity_name = None
            electricity_float = None
            quarter_heating_energy = None
            quarter_electricity = None
            print(f'ERROR: The final energy balance for the project {project_name} must be checked! '
                  f'There is an error in the eLCA data set for the selected energy sources. '
                  f'Please delete all data created so far by executing the function "delete_projects()". '
                  f'Then start DisteLCA again and select another energy carrier or electricity source.')

        operation_frame.loc[len(operation_frame)] = [project_name, heating_supplier, heating_float, electricity_name,
                                                     electricity_float, quarter_heating_energy, quarter_electricity]

        # life_cycle_inventory for materials
        # Read table ranking mass from eLCA and create dataframe
        soup_LCI = create_post_soup(session, 'https://www.bauteileditor.de/project-report-assets/topAssets/',
                                    'Elca\\View\\Report\\ElcaReportAssetsView', data={
                # Allow to show up to 1000 materials at the same time to read all
                'limit': '1000',
                # Present the materials in descending order with respect to mass
                'order': 'DESC',
                'inTotal': '1'
            })
        # Retrieve table input
        table_masses = soup_LCI.find('table', attrs={'class': 'report report-top-elements'})
        # Retrieve table headers and append them to a list of headers used for the new pandas dataframe
        titles = []
        for i in table_masses.find('thead').find('tr').find_all('th'):
            title = i.text
            titles.append(title)
        # Create pandas dataframe with table headers as columns
        masses_df = pd.DataFrame(columns=titles)
        # Create a for loop to fill mydata
        for j in table_masses.find('tbody').find_all('tr'):
            # fill dataframe row by row
            row_data = j.find_all('td')
            row = [i.text for i in row_data]
            length = len(masses_df)
            masses_df.loc[length] = row
        # Ranking row is not needed
        masses_df = masses_df.drop(columns=['#'])
        # Change type to float for further processing
        masses_df["Masse in kg"] = masses_df["Masse in kg"].str.replace(",", ".")
        masses_df = masses_df.astype({'Masse in kg': float})
        # Customise names of materials to indicate same materials throughout archetypes
        masses_df["Bauteil"] = masses_df["Bauteil"].str.extract(r"(.*) \[")
        masses_df['unit for component quantity and amount of component on quarter scale'] = masses_df[
            'Menge Bauteil'].str.extract(r"\d+\,\d+(.*)")
        masses_df['Menge Bauteil'] = masses_df['Menge Bauteil'].str.extract(r"(\d+\,\d+)")
        masses_df['Menge Bauteil'] = masses_df['Menge Bauteil'].str.replace(",", ".")
        masses_df = masses_df.astype({'Menge Bauteil': float})
        masses_df['amount building element on quarter scale'] = masses_df['Menge Bauteil'] * no_in_quarter
        masses_df['mass on quarter scale in kg'] = masses_df['Masse in kg'] * no_in_quarter
        masses_df = masses_df.rename(columns={'Prozess': 'process', 'Modul': 'module', 'Bauteil': 'component',
                                              'Menge Bauteil': 'component quantity',
                                              'Kostengruppe': 'cost group DIN 276', 'Masse in kg': 'mass in kg'})

        # Append dataframe to dictionary with project names as key and dataframe as value
        masses_frames_dict.update({project_name: masses_df})
        create_table(masses_df, f'district_reports//life_cycle_inventory//{no_spaces_name}_materials')

    print('Life Cycle Inventory: Tables on masses of building materials created!')

    # Show operational phase data
    create_table(operation_frame, 'district_reports//life_cycle_inventory//building_operation')

    # Show user input
    df_user_input = pd.DataFrame.from_dict(archetypes)
    create_table(df_user_input, 'district_reports//life_cycle_inventory//user_input')
    print('Life Cycle Inventory: User Input Table created!')
