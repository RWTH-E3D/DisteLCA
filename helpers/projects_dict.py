import re
from DisteLCA.helpers.beautifulsoup import create_get_soup
import requests

def projects_dict(session: requests.sessions) -> dict:
    """
    Create a dictionary of projects in a specific eLCA Bauteileditor account
    with project IDs as keys and project names as values
    :param session: Login session to read the projects
    """

    try:
        # Read projects in the account
        projects = {}
        projects_soup = create_get_soup(session, 'https://www.bauteileditor.de/projects','Elca\\View\\ElcaProjectsView')
        for project_tag in projects_soup.find('ul', {"class": "project-list"}).children:
            # Save project name
            project_name = project_tag.find('h2', {"class": "headline"}).text
            #
            if project_name == "Template creation":
                continue
            # Save project ID
            project_id = re.search(r".*-(\d*)", project_tag.attrs["id"]).group(1)
            # Update projects dictionary with IDs as keys and names as values
            projects.update({project_id: project_name})

        return projects
        #  If there are no projects in the account return empty dictionary
    except AttributeError:
        return None

