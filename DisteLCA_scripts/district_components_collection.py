from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup
from DisteLCA.helpers import login, save_component_json


def collect_district_templates():
    """
    DisteLCA accesses the specified account and reads out all private templates on eLCA outer walls,
    inner walls, ceilings, roofs, foundations, windows, and heating supply systems.
    """

    print(
        "The disteLCA programme has been started. The component templates from eLCA are read in. In a few seconds the "
        "graphical user interface will be displayed.")
    session = login()
    # german website is default
    # english_website = session.get('https://www.bauteileditor.de/lang/?lang=en')
    # change to english website requires changes on webscraping

    templates: list[dict] = []
    # These elements are excluded in DisteLCA, as they do not allow independent modelling of window and wall
    wrong_elements = [
        "2016_AW_mit_Fenster_Beispiel",
        "m²_Fenster / Isoglas 2-Scheiben / Alurahmen",
        "Stück_Fenster_1,6m² / Isoglas 2-Scheiben / Alurahmen",
        "Außenwand / einschaliges Mauerwerk / WDVS mit Fenster"
    ]
    # IDs for the component categories to be selected and read
    # First, the IDs of the various templates are retrieved, as these are needed to access
    # the further information about the templates in eLCA
    component_groups: list[tuple[str, str]] = [("foundation", "237"), ("outer_walls", "246"), ("roofs", "269"),
                                               ("windows", "250"), ("interior walls", "256"), ("ceilings", "264"),
                                               ("heating supply systems", "295")]

    # This dictionary entry is used if the necessary component is not available in the selection or out of scope
    def not_in_selection(group: str):
        templates.append(
            {"template_name": "Outside the scope of the study", "CG_DIN_276": group, "UUID": None,
             "description": None, "public": None, "U-Value": None})

    # This applies to all cost groups mirrored by disteLCA
    cgs = ["320", "330", "334", "340", "350", "360", "420"]
    for cg in cgs:
        not_in_selection(cg)

    for component, component_no in component_groups:
        # Create a function to read the names and IDs of the components in the eLCA templates
        def find_all_element_ids(response_text: str,
                                 filter_names: list[str] = None) -> list[int]:
            elements_view = json.loads(response_text)["Elca\\View\\ElcaElementsView"]
            elements_soup = BeautifulSoup(elements_view, "lxml")
            id_expr = re.compile(r"elca-sheet-(\d+)")
            name_expr = re.compile(r"(.+) \[\d+]")
            ids = []
            for element in list(elements_soup.find_all(name="div", attrs={"class": "elca-element-sheet"})):
                element_name = name_expr.search(element.find(name="h2", attrs={"class": "headline"}).text).group(1)
                # if the element name matches with any of the names of the defined wrong_elements, stop and don't append
                # this element id
                if filter_names and any(wrong_element == element_name for wrong_element in wrong_elements):
                    continue

                ids.append(re.search(id_expr, element.attrs["id"]).group(1))
            return ids

        first_page_response = session.post('https://www.bauteileditor.de/elements/list/', data={
            't': component_no,
            'search': '',
            'constrCatalogId': '',
            'constrDesignId': '',
            # "53" is Ökobaudat 2021 II ID
            'processDbId': '53',
            # Only private components should be read in, since only these
            # can ensure that they meet the requirements for modeling in
            # disteLCA. Public component templates are subject to change
            # over time that could generate an error output in disteLCA
            'scope': 'private'
        })
        # The components defined above, which can not be eco-balanced via disteLCA, are not
        # read in, this is ensured by the parameter filter_names
        element_ids = find_all_element_ids(first_page_response.text, filter_names=wrong_elements)
        # The display of the part templates can take up several pages in eLCA.
        # Therefore, all pages are read starting from page 1.
        # As soon as the "next_page_response" is no longer given (FALSE) the reading of parts is also interrupted.
        i = 1
        while True:
            next_page_response = session.get(
                f'https://www.bauteileditor.de/elements/list/?t={component_no}&page={i}',
                data={'t': component_no, 'page': i}
            )
            new_element_ids = find_all_element_ids(next_page_response.text, filter_names=wrong_elements)

            if not new_element_ids:
                break
            # Append to the List of element IDS
            element_ids.extend(new_element_ids)
            # Go to next page
            i += 1
        # Get more information about the component templates
        # Iterate through all components using their IDs
        for element_id in element_ids:
            # Enter the template page in eLCA
            element_response = session.get(f'https://www.bauteileditor.de/elements/{element_id}/')
            # Windows have a different html structure in eLCA than other components
            if component == "windows":
                # The JSON response has several sections, including: ElcaOsitView and ElcaElementView
                # For windows: the ElcaOsitView section contains the information on the cost group and the template name
                # ElcaElementView contains information on the description
                first_section_element_html = json.loads(element_response.text)["Elca\\View\\ElcaOsitView"]
                component_soup = BeautifulSoup(first_section_element_html, 'lxml')
                cost_group = re.search(r"(\d{3})", component_soup.find(name='a', attrs={'class': 'page'}).text).group(1)
                template_name = re.search(r"(.*) \[", component_soup.find(name='li', attrs={
                    'class': 'library active'}).span.text).group(1)
                try:
                    # Windows created via the window wizard in eLCA are represented by two different tabs.
                    # Through the second_window_tab_response the second tab is accessed
                    # The description of the window can only be accessed through this second tab
                    second_window_tab_response = session.get(
                        f'https://www.bauteileditor.de/elements/general/?e={element_id}&tab=general')
                    second_window_tab_html = json.loads(second_window_tab_response.text)["Elca\\View\\ElcaElementView"]
                    soup_second_window_tab: BeautifulSoup = BeautifulSoup(second_window_tab_html, 'lxml')
                    # Description of the template
                    description = soup_second_window_tab.textarea.text
                    template_u_value = \
                        soup_second_window_tab.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs['value']
                # Windows that are not created using the window wizard
                # (some windows of the public component templates, for example) have only one tab.
                # So if there is no second tab, an attribute or key error occurs and the description
                # of the window can be read in the original first tab
                except AttributeError or KeyError:
                    # JSON section ElcaElementView contains information on the description
                    second_section_element_html = json.loads(element_response.text)["Elca\\View\\ElcaElementView"]
                    soup_one_window_tab = BeautifulSoup(second_section_element_html, 'lxml')
                    description = soup_one_window_tab.textarea.text
                    template_u_value = \
                        soup_one_window_tab.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs['value']
                # At the beginning of the development of disteLCA, public templates were still included,
                # therefore the information about the publicity of the templates is
                # recorded in the dictionary for each component. In the further course of the software development,
                # the decision was made to include only private components.
                # All elements are private (see above)
                public = False
            else:
                # This section is for all other components
                first_section_element_html = json.loads(element_response.text)["Elca\\View\\ElcaElementView"]
                soup_element_information = BeautifulSoup(first_section_element_html, 'lxml')
                template_name_item = soup_element_information.find(name='input', attrs={'name': 'name'})
                template_name = template_name_item.attrs['value']
                # The public templates cannot be overwritten.
                # This can be used to determine whether the templates are public or private (see comment above)
                public = "readonly" in template_name_item.attrs
                # Retrieve description
                description = soup_element_information.textarea.text  # Beschreibung der Bauteilvorlage
                template_u_value = \
                    soup_element_information.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs['value']
                # Second section of the JSON response contains the cost group
                second_element_html = json.loads(element_response.text)['Elca\\View\\ElcaOsitView']
                soup_element_cost_group_information = BeautifulSoup(second_element_html, 'lxml')
                cost_group = re.search(r"(\d{3})", soup_element_cost_group_information.find(name='a', attrs={
                    'class': 'page'}).text).group(1)
            # Append all information to dictionary
            # This information is necessary to create projects in eLCA through CSV-Import
            # only the information on publicity is not necessary
            if template_u_value == "":
                template_u_value = "no information in eLCA"
            if description == "":
                description = "no information in eLCA"
            element_dict = {"template_name": template_name, "CG_DIN_276": cost_group, "UUID": element_id,
                            "description": description, "public": public, "U-Value": template_u_value}

            templates.append(element_dict)

    save_component_json(templates, "templates")

    print('All templates for components and energy sources have been read out!')
