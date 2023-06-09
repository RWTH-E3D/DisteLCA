import json
import bs4
from bs4 import BeautifulSoup
import requests
from typing import Union, Any



def create_get_soup(session: requests.sessions, URL: str, directory: str, data: dict = None, params: tuple[tuple[str, Union[str, Any]], tuple[str, str], tuple[str, str], tuple[str, str]]  = None) -> bs4.BeautifulSoup:
    """

    This function creates a BeautifulSoup object. The BeautifulSoup object represents the parsed document in its
    entirety.To create the Beautiful Soup object, the URL from which the BeautifulSoup is to be created must
    first be specified and then the section on this website under which it is to be searched is determined.
    Here a get request is executed.
    :param session: Login session for the request
    :param URL: URL to request
    :param directory: section of the website source code
    :param data: data to be sent with the get request
    :param params: params to be sent with the get request
    """

    # Retrieve URL get response
    response = session.get(URL, data=data, params=params)
    # Parse the response with json.loads and enter required section
    html = json.loads(response.text)[directory]
    # Create a BeautifulSoup object from the json data
    soup = BeautifulSoup(html, 'lxml')
    # Return BeautifulSoup object
    return soup

def create_post_soup(session: requests.sessions, URL: str, directory: str, data: dict = None, params: tuple[tuple[str, Union[str, Any]], tuple[str, str], tuple[str, str], tuple[str, str]]  = None) -> bs4.BeautifulSoup:
    """

    This function creates a BeautifulSoup object. The BeautifulSoup object represents the parsed document in its
    entirety.To create the Beautiful Soup object, the URL from which the BeautifulSoup is to be created must
    first be specified and then the section on this website under which it is to be searched is determined.
    Here a post request is executed.
    :param session: Login session for the request
    :param URL: URL to request
    :param directory: section of the website source code
    :param data: data to be sent with the post request
    :param params: params to be sent with the post request
    """

    # Retrieve URL post response
    response = session.post(URL, data=data, params=params)
    # Parse the response with json.loads and enter required section
    html = json.loads(response.text)[directory]
    # Create a BeautifulSoup object from the json data
    soup = BeautifulSoup(html, 'lxml')
    # Return BeautifulSoup object
    return soup