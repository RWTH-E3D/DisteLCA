import os
import json
import re
from glob import glob
from DisteLCA.helpers import login, create_get_soup


def create_district_projects():
    """
    Create projects in eLCA using the csv and json files. This information are send to the eLCA web server using post
    requests.
    """

    class eLCAProject:
        def __init__(self, project_dict):
            self.current_variant_id = None
            self.generation_response = None

            self.session = login()
            self.projectname = project_dict['projectname']
            self.gross_floor_area = project_dict['gross_floor_area']
            self.net_floor_area = project_dict['net_floor_area']
            self.energy_heating = project_dict['energy_heating']
            self.energy_water = project_dict['energy_water']
            self.energy_lighting = project_dict['energy_lighting']
            self.energy_source = project_dict['energy_source']

            self.create_through_csv_import()
            self.edit_created_project()

            # Outer walls have the code 246 in eLCA etc..
            component_elca_no = [246, 250, 269, 237, 256, 264, 295]
            for no in component_elca_no:
                self.save_components(no)
            self.add_final_energy_audit()

            print(f"Project {self.projectname} created!")

        def create_through_csv_import(self):

            filename = f"temp_data/{self.projectname}/{self.projectname}.csv"
            # Set parameter to import CSV file in eLCA
            files = {
                'importFile': (os.path.basename(filename), open(filename, 'rb'), "text/csv"),
            }
            # Data for CSV import project creation
            # Post data to eLCA server through post response with requests
            response_validate = self.session.post('https://www.bauteileditor.de/project-csv/validate/',
                                                  files=files,
                                                  data={
                                                      'name': self.projectname,
                                                      # private construction measure
                                                      'constrMeasure': "1",
                                                      # generic postcode
                                                      'postcode': "12345",
                                                      # single family homes
                                                      'constrClassId': "210",
                                                      # Benchmark system BNB-BN_2015 has the Version ID "6"
                                                      'benchmarkVersionId': "6",
                                                      # net floor space
                                                      'netFloorSpace': self.net_floor_area,
                                                      # gross floor space
                                                      'grossFloorSpace': self.gross_floor_area,
                                                      'upload': "Absenden"
                                                  })

            # Create dictionary for POST data to confirm component collection from CSV
            element_data = {}
            # Load preview of the components to create the project to retrieve data from the source code
            preview_soup = create_get_soup(self.session, 'https://www.bauteileditor.de/project-csv/preview/',
                                           'Elca\\View\\Import\\Csv\\ProjectImportPreviewView')
            for item in preview_soup.find_all('li', {"class": "element"}):
                item_name = item.find('span').text
                # Reading the KGR 2. level of the cost group (e.g. 330)
                item_cg_two = re.search(r"option selected=\"\" value=\"(\d{3})\">",
                                        str(item('select')[0].contents)).group(1)
                # Reading the KGR 3. level of the cost group, if available (e.g. 334)
                try:
                    examine_third_level = re.search(r"option selected=\"\" value=\"(\d{3})\">",
                                                    str(item('select')[1].contents)).group(1)
                    item_cg_three = examine_third_level
                    # if Attribute Error occurs there is no third level
                except AttributeError:
                    item_cg_three = ""
                # Reading element quantity and unit (m2/ Stück)
                item_quantity = item.input.attrs["value"]
                item_unit = re.search(r"option selected=\"\" value=\"(.*?)\">", str(item('select')[2].contents)).group(
                    1)
                # Reading the rel_id of the elements (long element ID)
                rel_id = re.search(r"relId=(.{8}-.{4}-.{4}-.{4}-.{12})", item.a.attrs["href"]).group(1)
                # Reading the short element ID of each element
                tpl_element_id = item('input')[1].attrs["value"]
                # Reading the description of each element
                designation = item.a.attrs["title"]
                # Fill POST data dictionary with the information read about elements
                element_data.update({
                    'dinCode2[{}]'.format(rel_id): item_cg_two,
                    'dinCode3[{}]'.format(rel_id): item_cg_three,
                    'quantity[{}]'.format(rel_id): item_quantity,
                    'unit[{}]'.format(rel_id): item_unit,
                    # short ID
                    'tplElementId[{}]'.format(rel_id): tpl_element_id
                })
            # Post data dictionary to confirm, project creation requires this at the end
            element_data.update({'createProject': 'Projekt erstellen'})
            # Create projects by confirming the components with the element_data
            # Project creation through POST request
            self.generation_response = self.session.post('https://www.bauteileditor.de/project-csv/preview/',
                                                         data=element_data)
            # Project is now created!
            return

        def edit_created_project(self):
            # Editing created project
            project_id_text = json.loads(self.generation_response.text)["Elca\\View\\ElcaModalProcessingView"]
            # Read the project ID
            project_id = re.search(r"data-action=\"/project-data/lcaProcessing/\?id=(\d{1,7})&amp",
                                   project_id_text).group(
                1)
            # Get request to update self.session headers and enter the project just created
            document = self.session.get(f'https://www.bauteileditor.de/projects/{project_id}/')

            # At each section of the project, the "Save" button must also be selected automatically
            # after creation so that the information is included in the life cycle assessment.
            # Read variant ID to make POST request on saving master data - general
            general_soup = create_get_soup(self.session, 'https://www.bauteileditor.de/project-data/general/',
                                           'Elca\\View\\ElcaProjectDataGeneralView')
            # Variant ID indicates planning phase - disteLCA only uses variant "preliminary planning"
            self.current_variant_id = \
                general_soup.find('div', {'class': 'form-section HtmlSelectbox-section currentVariantId'}).find(
                    'option',
                    text="-- Bitte wählen --").find_next_sibling(
                    name='option').attrs["value"]
            # Save and specify "existing building" project master data - general
            # and specify it as "existing building" to be able to tick the "Bestand" boxes
            general_save_data = {
                'name': self.projectname,
                'projectNr': '',
                # private constrcution measure
                'constrMeasure': '1',
                # Evaluation period 50 years
                'lifeTime': '50',
                # Building classification: single-family houses for residential purposes only
                'constrClassId': '210',
                # specify "existing building"
                # 'isExtantBuilding': 'true',
                'description': '',
                'street': '',
                # generic postcode
                'postcode': '12345',
                'city': '',
                'editor': '',
                'bnbNr': '',
                'eGisNr': '',
                # Deselect the BNB system evaluation (see above)
                'benchmarkVersionId': '',
                # 53 is Ökobaudat 2021 II
                'processDbId': '53',
                'currentVariantId': self.current_variant_id,
                'constrCatalogId': '',
                'constrDesignId': '',
                'livingSpace': '',
                'netFloorSpace': self.net_floor_area,
                'grossFloorSpace': self.gross_floor_area,
                'floorSpace': '',
                'propertySize': '',
                'pw': '',
                'pwRepeat': '',
                'save': 'Speichern'
            }
            # Save master data - general through post request
            response_save = self.session.post('https://www.bauteileditor.de/project-data/save/', data=general_save_data)

        def save_components(self, elca_component_category_id: int):
            # enter list of components of the project just created in this URL through get request
            components_soup = create_get_soup(self.session,
                                              f'https://www.bauteileditor.de/project-elements/list/?t={elca_component_category_id}',
                                              'Elca\\View\\ElcaProjectElementsView')
            # Make list of all components of the certain category (walls, roofs or windows)
            components = []
            for item in components_soup.find_all(name='h2', attrs={'class': 'headline'}):
                # Read the ID of the component
                component_id = re.search(r"(\d{7})", item.text).group(1)
                # Append the ID to the list
                components.append(component_id)
            # Iterate through list of components to save all components
            for component in components:
                # The disteLCA window templates created through the window wizard have a
                # different saving data structure than the other components (see under except)
                # All windows created without the window wizard and all roofs and outer
                # walls have the code structure to be saved with the code in "try section"
                try:
                    # This is the code for  windows created without the
                    # window wizard and all other components
                    # Enter the component
                    component_soup = create_get_soup(self.session,
                                                     f'https://www.bauteileditor.de/project-elements/{component}/',
                                                     'Elca\\View\\ElcaElementView')
                    # Retrieve component name
                    component_name = component_soup.find(name='input', attrs={'name': 'name'}).attrs['value']
                    # Retrieve component quantity
                    component_quantity = component_soup.find(name='input', attrs={'name': 'quantity'})[
                        'value']
                    # Retrieve component description
                    component_description = component_soup.textarea.text
                    # Retrieve component U-Value
                    component_uvalue = component_soup.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs[
                        'value']
                    # Windows (ID=250) have the unit "Stück" while other components have the unit "m2"
                    if elca_component_category_id == 250:
                        component_unit = 'Stück'
                    elif elca_component_category_id == 295:
                        component_unit = 'Stück'
                    else:
                        component_unit = 'm2'
                    # Create dictionary for the data that has to be sent to the eLCA server to
                    # save the components through post request
                    component_save_data = {
                        # Variant ID indicates planning phase - disteLCA only uses variant "preliminary planning"
                        'projectVariantId': self.current_variant_id,
                        'elementId': component,
                        'name': component_name,
                        'attr[elca.oz]': '',
                        'description': component_description,
                        'quantity': component_quantity,
                        'refUnit': component_unit,
                        'attr[elca.uValue]': component_uvalue,
                        # R-Value could be specified, but it's not necessary
                        'attr[elca.rW]': '',
                        # Dismantling (Rückbau), separation (Trennung) and recycling
                        # (Verwertung) factors can be specified
                        # to evaluate the Dismantling, separation and recycling criterion of the BNB System.
                        # This is not used in disteLCA
                        'attr[elca.bnb.eol]': '',
                        'attr[elca.bnb.separation]': '',
                        'attr[elca.bnb.recycling]': '',
                        'saveElement': 'Speichern'
                    }
                    # Save component of the project
                    save_component_response = self.session.post(
                        'https://www.bauteileditor.de/project-elements/save/',

                        data=component_save_data)
                except KeyError:
                    # Windows created with the window wizard
                    # Retrieve information through Beautiful Soup
                    # Windows created through the window wizard can contain a lot of information about
                    # frames, gaskets, fittings, etc., all of which must be retrieved and saved in the next step.
                    window_soup = create_get_soup(self.session,
                                                  f'https://www.bauteileditor.de/project-elements/{component}/',
                                                  'Elca\\View\\Assistant\\WindowAssistantView')
                    # Information on the window name
                    window_name = window_soup.find(name='input', attrs={'name': 'name'}).attrs['value']
                    # Window width
                    window_width = window_soup.find(name='input', attrs={'name': 'width'}).attrs['value']
                    # Window height
                    window_height = window_soup.find(name='input', attrs={'name': 'height'}).attrs['value']
                    # Sealing (Abdichtung)
                    window_sealing_width = window_soup.find(name='input', attrs={'name': 'sealingWidth'}).attrs[
                        'value']
                    # More data on the specific window
                    # Blind frame width
                    fixedFrameWidth = window_soup.find(name='input', attrs={'name': 'fixedFrameWidth'}).attrs[
                        'value']
                    # Sash width
                    sashFrameWidth = window_soup.find(name='input', attrs={'name': 'sashFrameWidth'}).attrs['value']
                    # Mullions and transoms
                    numberOfMullions = window_soup.find(name='input', attrs={'name': 'numberOfMullions'}).attrs[
                        'value']
                    numberOfTransoms = window_soup.find(name='input', attrs={'name': 'numberOfTransoms'}).attrs[
                        'value']
                    # ID of blind frame material
                    processConfigId_fixedFrame = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[fixedFrame]'}).attrs['value']
                    # ID of sash frame material
                    processConfigId_sashFrame = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[sashFrame]'}).attrs['value']
                    # ID of glass type
                    processConfigId_glass = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[glass]'}).attrs[
                            'value']
                    # ID of sealing material
                    processConfigId_sealing = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[sealing]'}).attrs[
                            'value']
                    # ID of fittings
                    processConfigId_fittings = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[fittings]'}).attrs[
                            'value']
                    # Name of fittings
                    fittings = window_soup.find(name='input', attrs={'name': 'fittings'}).attrs['value']
                    # ID of handles
                    processConfigId_handles = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[handles]'}).attrs[
                            'value']
                    # Name of handles
                    handles = window_soup.find(name='input', attrs={'name': 'handles'}).attrs['value']
                    # ID of sun shade
                    processConfigId_sunscreenOutdoor = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[sunscreenOutdoor]'}).attrs[
                            'value']
                    # ID of glare shield
                    processConfigId_sunscreenIndoor = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[sunscreenIndoor]'}).attrs[
                            'value']
                    # ID of interior windowsill
                    processConfigId_sillIndoor = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[sillIndoor]'}).attrs['value']
                    # Size of interior windowsill
                    sillIndoorSize = window_soup.find(name='input', attrs={'name': 'sillIndoorSize'}).attrs['value']
                    # Depth of interior windowsill
                    sillIndoorDepth = window_soup.find(name='input', attrs={'name': 'sillIndoorDepth'}).attrs[
                        'value']
                    # ID of interior window soffit
                    processConfigId_soffitIndoor = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[soffitIndoor]'}).attrs[
                            'value']
                    # Size of interior window soffit
                    soffitIndoorSize = window_soup.find(name='input', attrs={'name': 'soffitIndoorSize'}).attrs[
                        'value']
                    # Depth of interior window soffit
                    soffitIndoorDepth = window_soup.find(name='input', attrs={'name': 'soffitIndoorDepth'}).attrs[
                        'value']
                    # ID of exterior windowsill
                    processConfigId_sillOutdoor = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[sillOutdoor]'}).attrs[
                            'value']
                    # Size of exterior windowsill
                    sillOutdoorSize = window_soup.find(name='input', attrs={'name': 'sillOutdoorSize'}).attrs[
                        'value']
                    # Depth of exterior windowsill
                    sillOutdoorDepth = window_soup.find(name='input', attrs={'name': 'sillOutdoorDepth'}).attrs[
                        'value']
                    # ID of exterior window soffit
                    processConfigId_soffitOutdoor = \
                        window_soup.find(name='input', attrs={'name': 'processConfigId[soffitOutdoor]'}).attrs[
                            'value']
                    # Size of exterior window soffit
                    soffitOutdoorSize = window_soup.find(name='input', attrs={'name': 'soffitOutdoorSize'}).attrs[
                        'value']
                    # Depth of exterior window soffit
                    soffitOutdoorDepth = window_soup.find(name='input', attrs={'name': 'soffitOutdoorDepth'}).attrs[
                        'value']

                    # create dictionary with all the window data
                    window_save_data = {
                        'context': 'project-elements',
                        'projectVariantId': self.current_variant_id,
                        'e': component,
                        'name': window_name,
                        'width': window_width,
                        'height': window_height,
                        'sealingWidth': window_sealing_width,
                        'fixedFrameWidth': fixedFrameWidth,
                        'sashFrameWidth': sashFrameWidth,
                        'numberOfMullions': numberOfMullions,
                        'numberOfTransoms': numberOfTransoms,
                        'processConfigId[fixedFrame]': processConfigId_fixedFrame,
                        'processConfigId[sashFrame]': processConfigId_sashFrame,
                        'processConfigId[glass]': processConfigId_glass,
                        'processConfigId[sealing]': processConfigId_sealing,
                        'processConfigId[fittings]': processConfigId_fittings,
                        'fittings': fittings,
                        'processConfigId[handles]': processConfigId_handles,
                        'handles': handles,
                        'processConfigId[sunscreenOutdoor]': processConfigId_sunscreenOutdoor,
                        'processConfigId[sunscreenIndoor]': processConfigId_sunscreenIndoor,
                        'processConfigId[sillIndoor]': processConfigId_sillIndoor,
                        'sillIndoorSize': sillIndoorSize,
                        'sillIndoorDepth': sillIndoorDepth,
                        'processConfigId[soffitIndoor]': processConfigId_soffitIndoor,
                        'soffitIndoorSize': soffitIndoorSize,
                        'soffitIndoorDepth': soffitIndoorDepth,
                        'processConfigId[sillOutdoor]': processConfigId_sillOutdoor,
                        'sillOutdoorSize': sillOutdoorSize,
                        'sillOutdoorDepth': sillOutdoorDepth,
                        'processConfigId[soffitOutdoor]': processConfigId_soffitOutdoor,
                        'soffitOutdoorSize': soffitOutdoorSize,
                        'soffitOutdoorDepth': soffitOutdoorDepth,
                        'saveElement': 'Speichern'
                    }
                    # save the windows with the data from the dictionary
                    response_save_window = self.session.post('https://www.bauteileditor.de/assistant/window/save/',
                                                             data=window_save_data)

        # Save components

        def add_final_energy_audit(self):
            # Add final energy audit
            # Update headers to enter final energy input page
            enev_response = self.session.get('https://www.bauteileditor.de/project-data/enEv/')
            # Save the energy demand and specify net floor area according to EnEV
            ngf_enev_response = self.session.post('https://www.bauteileditor.de/project-data/saveEnEv/', data={
                'projectVariantId': self.current_variant_id,
                'addDemand': '',
                'addEnergyDemand': 'Bedarf hinzufügen',
                # Specify net floor area according to EnEV assumption ngfnev = ngf
                'ngf': self.net_floor_area,
                'enEvVersion': ''
            })

            # Specify energy source and save
            def specify_final_energy_audit(carrier_id, heating, water, lighting):
                energy_response = self.session.post('https://www.bauteileditor.de/project-data/selectProcessConfig/',
                                                    data={
                                                        'relId': 'newDemand',
                                                        'projectVariantId': self.current_variant_id,
                                                        'ngf': self.net_floor_area,
                                                        'enEvVersion': '',
                                                        'headline': 'Baustoff suchen und wählen',
                                                        'p': '',
                                                        'sp': '',
                                                        # 53 is Ökobaudat 2021 II
                                                        'db': '53',
                                                        'filterByProjectVariantId': '',
                                                        'tpl': '',
                                                        'b': 'operation',
                                                        'u': 'kWh',
                                                        'search': '',
                                                        # Category 8.06 Usage: Selections from this only.
                                                        'processCategoryNodeId': '679',
                                                        # retrive energy carrier ID chosen by user in GUI
                                                        'id': carrier_id,
                                                        'select': 'Übernehmen'
                                                    })
                # Specify end energy for heating and warm water

                end_energy_response = self.session.post('https://www.bauteileditor.de/project-data/saveEnEv/', data={
                    'projectVariantId': self.current_variant_id,
                    # only one energy carrier in disteLCA
                    'addDemand': '1',
                    # energy carrier from JSON data
                    'processConfigId[newDemand]': carrier_id,
                    # energy need for heating from JSON data
                    'heating[newDemand]': heating,
                    # energy need for hot water from JSON data
                    'water[newDemand]': water,
                    'lighting[newDemand]': lighting,
                    # 'lighting[newDemand]': electricity_demand,
                    'ventilation[newDemand]': '',
                    'cooling[newDemand]': '',
                    'isKwk[newDemand]': '',
                    'saveEnergyDemand': 'Speichern',
                    # Net floor area
                    'ngf': self.net_floor_area,
                    'enEvVersion': ''
                })

            # Heating and hot water
            specify_final_energy_audit(self.energy_source, self.energy_heating, self.energy_water, '')
            # Lighting
            # retrieve energy carrier ID chosen by user in GUI electricity is 15557
            specify_final_energy_audit('15557', '', '', self.energy_lighting)

    all_archetype_folders = glob("temp_data/*/")
    all_projects = []
    for archetype_folder in all_archetype_folders:
        archetype_name = archetype_folder.split("\\")[1]
        archetype_data = f"{archetype_folder}{archetype_name}.json"
        with open(archetype_data, encoding="utf-8") as file:
            all_projects.append(json.load(file))
    for project in all_projects:
        eLCAProject(project)

    print("All projects have been created!")
