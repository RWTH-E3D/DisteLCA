import requests
import json

def login() -> requests.Session:
    """
    login to specific eLCA Bauteileditor account and return requests session to stay
    logged in for further requests
    :param username: Username of the eLCA account
    :param password: Password of the eLCA account
    """

    lc = open("temp_data/login_credentials.json", encoding="utf-8")
    login_credentials = json.load(lc)

    username = login_credentials["User name"]
    password = login_credentials["Password"]

    session = requests.session()
    headers = {'x-requested-with': 'XMLHttpRequest'}
    session.headers.update(headers)

    response_import = session.post("https://www.bauteileditor.de/login/", data={
        "origin": "/",
        "authName": username,
        "authKey": password,
        "login": "Absenden"
    })
    if "authName error" in response_import.text:
        raise ValueError("Login was unsuccessful.")
    return session
