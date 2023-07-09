# -*- coding: utf-8 -*-
"""
Author: Antonio Ventilii
"""

import easygui
import keyring


def credentials(service_name: str) -> tuple[str, str]:
    """
    Retrieves or prompts for credentials associated with a service.

    Args:
        service_name (str): The name of the service.

    Returns:
        tuple[str, str]: A tuple containing the username and password.

    """

    # Get the stored credentials for the given service name
    c = keyring.get_credential(service_name, None)
    if c is None:
        text = f"Enter '{service_name}' Credentials:"
        title = 'Credentials'
        fields = ['Email', 'Password']

        # Prompt the user to enter their credentials using a GUI dialog
        username, password = easygui.multpasswordbox(text, title, fields)

        # Store the entered credentials securely using the keyring library
        keyring.set_password(service_name, username, password)
    else:
        # Retrieve the stored username and password from the keyring library
        username = c.username
        password = c.password
    return username, password
