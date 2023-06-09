import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from DisteLCA_scripts.login_credentials import create_login_gui
from DisteLCA_scripts.district_components_collection import collect_district_templates
from DisteLCA_scripts.district_gui import create_district_gui
from DisteLCA_scripts.district_data_preparation import prepare_district_data
from DisteLCA_scripts.district_projects_creation import create_district_projects
from DisteLCA_scripts.district_lci import compile_district_lci
from DisteLCA_scripts.district_lcia import calculate_district_lcia
from DisteLCA_scripts.gui_district_delete import delete_district_projects

def main():

    """

    DisteLCA is a Python 3.9 tool that facilitates creating multiple projects in the eLCA Bauteileditor (eng. component
    editor) Version 0.9.7. The eLCA Bauteileditor is a web-based Software to generate life
    cycle assessments of buildings administered by the German Federal Institute for Research on Building, Urban Affairs,
    and Spatial Development (BBSR). At the moment, DisteLCA enables the assessment of exterior walls,
    windows, roofs, ceilings, inner walls, foundations, and heat supply systems, as well as the operational energy use.
    DisteLCA targets time savings in using eLCA for districts without compromising its fidelity of the results for
    individual buildings. The different functions are executed one after the other.

    """

    # To initiate DisteLCA, a user has to submit eLCA login credentials
    create_login_gui()
    # Access the provided account to read out all private templates
    collect_district_templates()
    # The user can enter information on the different building archetypes of the district
    create_district_gui()
    # DisteLCA processes the user input to the formats necessary for project creation through CSV import.
    prepare_district_data()
    # The projects on the district archetypes are created automatically in the specified eLCA account.
    create_district_projects()
    # LCI data is web scaped from eLCA and compiled
    compile_district_lci()
    # LCIA data is web scaped from eLCA and compiled
    calculate_district_lcia()
    # Delete data for next programme start
    delete_district_projects()


if __name__ == '__main__':
    main()



