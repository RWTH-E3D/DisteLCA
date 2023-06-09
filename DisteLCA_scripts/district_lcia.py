import re
from typing import Union, Any
import pandas as pd
from DisteLCA.helpers import load_component_json, login, create_get_soup, projects_dict, create_table, reorder_dataframe, \
    create_district_report_dirs


def calculate_district_lcia():
    """
    Enter the specified eLCA account and the projects just created. Read out the evaluation data on the life cycle
    impact assessment of the projects. Compile them into tables and upscale data to the district level by multiplying
    the single building results with the number of buildings of that archetype in the district. Save all results in
    CSV files.  The results for the life cycle impact assessment in DisteLCA give an overview of the summarized GWPs
    for materials and building operation, the results for the different life cycle modules, and all building
    materials and components.
    """
    create_district_report_dirs()
    archetypes: list[dict] = load_component_json("archetypes")
    session = login()
    overall_district_gwp = 0
    overall_district_gwp_b6 = 0
    overall_district_gwp_construction = 0
    overall_district_gwp_systems = 0

    projects = projects_dict(session)
    for project_id, project_name in projects.items():
        no_spaces_name = project_name.replace(' ', '')
        no_in_quarter = (next((item for item in archetypes if item['archetype name'] == project_name), None))[
            'occurrence in the quarter']
        net_ground_space = (next((item for item in archetypes if item['archetype name'] == project_name), None))[
            'NFA in m²']
        # Enter project to update header
        project_overview_response = session.get("https://www.bauteileditor.de/projects/{}/".format(project_id))
        summary_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-reports/summary/',
                                       'Elca\\View\\Report\\ElcaReportSummaryView')
        gwp_tabelle = summary_soup.find('table', {'class': 'GPWtabelle'})  # Achtung typo!
        # Retrieve total GWP
        gwptotal = gwp_tabelle.find('td', text="GWP").find_next_sibling(name='td', attrs={'class': 'lastColumn'}).text
        # Retrieve GWP of module B6
        try:
            gwpb6 = gwp_tabelle.find('td', text="B6").find_next_sibling(name='td', attrs={'class': 'lastColumn'}).text
        except AttributeError:
            gwpb6 = None
        # Retrieve GWP of constrcution (walls, windows and roof)
        try:
            gwpkg300 = gwp_tabelle.find('td', text="KG 300").find_next_sibling(name='td',
                                                                               attrs={'class': 'lastColumn'}).text
        except AttributeError:
            gwpkg300 = None
        try:
            gwpkg400 = gwp_tabelle.find('td', text="KG 400").find_next_sibling(name='td',
                                                                               attrs={'class': 'lastColumn'}).text
        except AttributeError:
            gwpkg400 = None

        def string_to_float(str):
            try:
                float_value = float(str.replace(',', '.'))
            except AttributeError:
                float_value = None
            return float_value

        gwptotal_float = string_to_float(gwptotal)
        gwpb6_float = string_to_float(gwpb6)
        gwpkg300_float = string_to_float(gwpkg300)
        gwpkg400_float = string_to_float(gwpkg400)

        def district_upscale(single_building_value, no, ngs):
            try:
                quarter_float = round(single_building_value * no * ngs, 2)
            except TypeError:
                quarter_float = None
            return quarter_float

        dist_gwptotal = district_upscale(gwptotal_float, no_in_quarter, net_ground_space)
        dist_gwpb6 = district_upscale(gwpb6_float, no_in_quarter, net_ground_space)
        dist_gwpkg300 = district_upscale(gwpkg300_float, no_in_quarter, net_ground_space)
        dist_gwpkg400 = district_upscale(gwpkg400_float, no_in_quarter, net_ground_space)

        # Create dictionary from information of overall balance
        overall_project = {
            f'total district ({no_in_quarter} buildings x {net_ground_space} m²)': dist_gwptotal,
            'one building': gwptotal_float,
            'module B6 district scale': dist_gwpb6,
            'module B6 per building': gwpb6_float,
            'construction (CG 300 of DIN 276) district scale': dist_gwpkg300,
            'construction (CG 300 of DIN 276) per building': gwpkg300_float,
            'systems (CG 400 of DIN 276) district scale': dist_gwpkg400,
            'systems (CG 400 of DIN 276) per building': gwpkg400_float}

        df_overall_gwp = pd.DataFrame.from_dict(overall_project, orient='index')
        df_overall_gwp['area'] = df_overall_gwp.index
        df_overall_gwp.reset_index(drop=True, inplace=True)
        df_overall_gwp = df_overall_gwp.rename(columns={0: 'GWP'})
        df_overall_gwp = reorder_dataframe(df_overall_gwp, [1, 0])
        df_overall_gwp['unit'] = 'kg CO2-eqv./m²a'
        df_overall_gwp.at[0, 'unit'] = 'kg CO2-eqv./a'
        df_overall_gwp.at[2, 'unit'] = 'kg CO2-eqv./a'
        df_overall_gwp.at[4, 'unit'] = 'kg CO2-eqv./a'
        df_overall_gwp.at[6, 'unit'] = 'kg CO2-eqv./a'
        create_table(df_overall_gwp, f'district_reports\life_cycle_impact\gwp_overview_{no_spaces_name}')
        print(f'GWP overview on {no_spaces_name} created!')

        # add values of the archetype to the overall district results
        if dist_gwptotal is not None:
            overall_district_gwp += dist_gwptotal
        if dist_gwpb6 is not None:
            overall_district_gwp_b6 += dist_gwpb6
        if dist_gwpkg300 is not None:
            overall_district_gwp_construction += dist_gwpkg300
        if dist_gwpkg400 is not None:
            overall_district_gwp_systems += dist_gwpkg400

        def find_total():
            total_indicator_values_list = []
            for x in range(14):
                total_indcator_value = \
                    summary_soup.find(name='table', attrs={'class': 'report report-effects'}).find(
                        name='tbody').find_all(
                        name='tr')[x].contents[2].text
                total_indicator_values_list.append(total_indcator_value)
            total_indicator_values_list = [v.replace(",", ".") for v in total_indicator_values_list]
            total_indicator_values_list = list(map(float, total_indicator_values_list))
            return total_indicator_values_list

        def find_module(class_name: str, table_no: int):
            indicator_values_list = []
            for x in range(14):
                indicator_value = \
                    summary_soup.find_all(name='li', attrs={'class': class_name})[table_no].find(name='tbody').find_all(
                        name='tr')[x].contents[2].text
                indicator_values_list.append(indicator_value)
            indicator_values_list = [v.replace(",", ".") for v in indicator_values_list]
            indicator_values_list = list(map(float, indicator_values_list))

            return indicator_values_list

        try:
            lca_modules = {
                'Indicator': ['GWP', 'ODP', 'POCP', 'AP', 'EP', 'Total PE', 'PENRT', 'PENRM', 'PENRE', 'PERT', 'PERM',
                              'PERE', 'ADP elem.', 'ADP fossil'],
                'Unit': ['kg CO2-eqv./m²a',
                         'kg R11 eqv./m²a',
                         'kg ethene eqv./m²a',
                         'kg SO2 eqv./m²a',
                         'kg PO4 eqv./m²a',
                         'MJ/m²a',
                         'MJ/m²a',
                         'MJ/m²a',
                         'MJ/m²a',
                         'MJ/m²a',
                         'MJ/m²a',
                         'MJ/m²a',
                         'kg Sb eqv./m²a',
                         'MJ/m²a'],
                'A1-A3': find_module('section clearfix', 0),
                'B4': find_module('section clearfix last', 1),
                'B6': find_module('section clearfix', 1),
                'C3': find_module('section clearfix', 2),
                'C4': find_module('section clearfix', 3),
                'total': find_total(),
                'D': find_module('section clearfix', 4)}
        except AttributeError:
            lca_modules = None

        df_lca_modules = pd.DataFrame(data=lca_modules)

        create_table(df_lca_modules, f'district_reports\life_cycle_impact\life_cycle_modules_{no_spaces_name}')
        print(f'Impact assessment {project_name}: Tables on life cycle modules have been created!')

        lcia_frame = pd.DataFrame(
            columns=['Life Cycle Impact Assessment', 'GWP', 'ODP', 'POCP', 'AP', 'EP', 'Total PE', 'PENRT', 'PENRM',
                     'PENRE', 'PERT', 'PERM',
                     'PERE', 'ADP elem.', 'ADP fossil'])

        elements_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-report-effects/construction/',
                                        'Elca\\View\\Report\\ElcaReportEffectsView')

        def find_material_indicators(material_level_soup: str):
            material_indic_list = []
            for x in range(14):
                material_indicator_value = \
                    material_level_soup.find(name='tbody').contents[x].find(name='td', attrs={'class': 'total'}).text
                material_indic_list.append(material_indicator_value)
            material_indic_list = [v.replace(",", ".") for v in material_indic_list]
            material_indic_list = list(map(float, material_indic_list))
            return material_indic_list

        try:
            for element in list(elements_soup.find('ul', attrs={'class': 'category'}).contents):
                element_category = element.find(name='h1').text
                element_name = element.find(name='a', attrs={'class': 'page'}).text
                element_id = re.search(r"\/project-elements\/(\d+)", element.find('a').attrs['href']).group(1)
                element_indicator_values = find_material_indicators(element)
                element_indicator_values.insert(0, f'Cost Group {element_category} : {element_name}')
                lcia_frame.loc[len(lcia_frame)] = element_indicator_values
                picture_size = re.search(
                    fr'/project-report-effects/elementDetails/\?e={element_id}&m2a=(\d+)&a=0&rec=0',
                    element.find('h3').attrs['data-url']).group(1)

                params = (
                    # ID of the element
                    ('e', element_id),
                    # picture size
                    ('m2a', picture_size),
                    ('a', '0'),
                    ('rec', '0'),
                )
                element_details_soup = create_get_soup(session,
                                                       'https://www.bauteileditor.de/project-report-effects/elementDetails/',
                                                       'Elca\\View\\Report\\ElcaReportEffectDetailsView', params=params)
                pattern1 = re.compile(r"\[\d+] \d{1,2}\.(.*)")
                pattern2 = re.compile(r"\d{1,2}\.(.*)")
                for detail in element_details_soup.find_all('li', attrs={'class': 'section clearfix'}):
                    detail_name_all = detail.find(name='h4').text
                    try:
                        detail_name = re.search(pattern1, detail_name_all).group(1)
                    except AttributeError:
                        try:
                            detail_name = re.search(pattern2, detail_name_all).group(1)
                        except AttributeError:
                            detail_name = detail_name_all

                    detail_indicator_values = find_material_indicators(detail)
                    detail_indicator_values.insert(0,
                                                   f'Cost Group {element_category} : {element_name} -> Baustoff {detail_name}')
                    lcia_frame.loc[len(lcia_frame)] = detail_indicator_values

        except AttributeError:
            pass
        systems_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-report-effects/systems/',
                                       'Elca\\View\\Report\\ElcaReportEffectsView')
        try:
            for system in list(systems_soup.find('ul', attrs={'class': 'category'}).contents):
                system_category = system.find(name='h1').text
                system_name = system.find(name='a', attrs={'class': 'page'}).text
                system_id = re.search(r"\/project-elements\/(\d+)", system.find('a').attrs['href']).group(1)
                system_indicator_values = find_material_indicators(system)
                system_indicator_values.insert(0, f'Cost Group {system_category} : {system_name}')
                lcia_frame.loc[len(lcia_frame)] = system_indicator_values
                system_picture_size = re.search(
                    fr'/project-report-effects/elementDetails/\?e={system_id}&m2a=(\d+)&a=0&rec=0',
                    system.find('h3').attrs['data-url']).group(1)

                params: tuple[tuple[str, Union[str, Any]], tuple[str, str], tuple[str, str], tuple[str, str]] = (
                    ('e', system_id),
                    ('m2a', system_picture_size),
                    ('a', '0'),
                    ('rec', '0'),
                )
                system_details_soup = create_get_soup(session,
                                                      'https://www.bauteileditor.de/project-report-effects/elementDetails/',
                                                      'Elca\\View\\Report\\ElcaReportEffectDetailsView', params=params)
                pattern1 = re.compile(r"\[\d+] \d{1,2}\.(.*)")
                pattern2 = re.compile(r"\d{1,2}\.(.*)")

                for system_detail in system_details_soup.find_all('li', attrs={'class': 'section clearfix'}):
                    system_detail_name_all = system_detail.find(name='h4').text
                    # system_detail_gwp = system_detail.find(name='tbody').find(name='td', attrs={'class': 'total'}).text
                    system_detail_indicator_values = find_material_indicators(system_detail)

                    try:
                        system_detail_name = re.search(pattern1, system_detail_name_all).group(1)
                    except AttributeError:
                        try:
                            system_detail_name = re.search(pattern2, system_detail_name_all).group(1)
                        except AttributeError:
                            system_detail_name = system_detail_name_all

                    system_detail_indicator_values.insert(0,
                                                          f'Cost Group {system_category} : {system_name} -> Baustoff {system_detail_name}')
                    lcia_frame.loc[len(lcia_frame)] = system_detail_indicator_values
        except AttributeError:
            pass

        create_table(lcia_frame, f'district_reports\life_cycle_impact\{no_spaces_name}_LCIA')
        print(f'Impact assessment {project_name}: Tables for impact assessment of the materials have been created!')

    # Create overview for the GWP of the whole district
    overall_district = {
        f'total district GWP of all archetypes': overall_district_gwp,
        'total district module B6': overall_district_gwp_b6,
        'total district construction (CG 300 of DIN 276)': overall_district_gwp_construction,
        'total district systems (CG 400 of DIN 276)': overall_district_gwp_systems}

    df_overall_district_gwp = pd.DataFrame.from_dict(overall_district, orient='index')
    df_overall_district_gwp['area'] = df_overall_district_gwp.index
    df_overall_district_gwp.reset_index(drop=True, inplace=True)
    df_overall_district_gwp = df_overall_district_gwp.rename(columns={0: 'GWP'})
    df_overall_district_gwp = reorder_dataframe(df_overall_district_gwp, [1, 0])
    df_overall_district_gwp['unit'] = 'kg CO2-eqv./a'
    df_overall_district_gwp = df_overall_district_gwp.replace({0.0: None})
    create_table(df_overall_district_gwp, f'district_reports\life_cycle_impact\gwp_total_district_overview')
    print('Impact assessment of GWP for the whole district compiled!')
