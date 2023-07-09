# -*- coding: utf-8 -*-
"""
Module containing custom functions related to web drivers.

Author: Antonio Ventilii
"""

import os
import shutil
from datetime import datetime

import requests
from requests import Response
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.http import HttpClient
from webdriver_manager.core.logger import log
from webdriver_manager.firefox import GeckoDriverManager

WebdriverType = webdriver.Firefox | webdriver.Chrome

CUSTOM_PROXIES = {
    'http': 'http://',
    'https': 'https://',
}

DEFAULT_USER_HOME_CACHE_PATH = os.path.join(os.path.expanduser('~'), '.cache')


def firefox_profile_path() -> str:
    """
    Returns the path to the Firefox profile folder.

    Returns:
        str: The path to the Firefox profile folder.
    """
    user = os.getlogin()
    firefox_profile = f'C:\\Users\\{user}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\vontobel.default'
    return firefox_profile


class CustomHttpClient(HttpClient):
    """
    Custom HTTP client for requests.
    """

    def get(self, url, params=None, **kwargs) -> Response:
        """
        Perform a GET request with custom logic like session or proxy.

        Args:
            url (str): The URL to send the GET request to.
            params (dict): The parameters to include in the GET request.
            **kwargs: Additional keyword arguments to pass to the requests library.

        Returns:
            Response: The response object from the GET request.
        """
        log("The call will be done with custom HTTP client")
        return requests.get(url, params, **kwargs, proxies=CUSTOM_PROXIES)


def download_manager() -> WDMDownloadManager:
    """
    Returns the download manager for WebDriverManager.

    Returns:
        WDMDownloadManager: The download manager for WebDriverManager.
    """
    http_client = CustomHttpClient()
    return WDMDownloadManager(http_client)


def chromedriver_path() -> str:
    """
    Returns the path to the ChromeDriver executable.

    Returns:
        str: The path to the ChromeDriver executable.
    """
    return ChromeDriverManager(download_manager=download_manager()).install()


def geckodriver_path() -> str:
    """
    Returns the path to the GeckoDriver executable.

    Returns:
        str: The path to the GeckoDriver executable.
    """
    return GeckoDriverManager(download_manager=download_manager()).install()


def firefox(headless: bool = False, use_local_profile: bool = False, save_local_profile_to_cache: bool = True,
            profile_folder: str = None, download_dir: str = None, verbose: bool = False,
            copy_threshold_days: int = 7) -> webdriver.Firefox:
    """
    Creates a Firefox WebDriver instance with custom options.

    Args:
        headless (bool): Whether to run Firefox in headless mode. Defaults to False.
        use_local_profile (bool): Whether to use the local Firefox profile. Defaults to False.
        save_local_profile_to_cache (bool): Whether to save the local Firefox profile to cache. Defaults to True.
        profile_folder (str): Path to the local Firefox profile folder. Defaults to None.
        download_dir (str): Directory path for downloads. Defaults to None.
        verbose (bool): Whether to display verbose output. Defaults to False.
        copy_threshold_days (int): Number of days within which the profile should be considered fresh. Defaults to 7.

    Returns:
        webdriver.Firefox: The created Firefox WebDriver instance.
    """
    if use_local_profile:
        if profile_folder:
            print('Profile folder was given but it will be overwritten by local profile.')
        src_folder = firefox_profile_path()
        if save_local_profile_to_cache:
            if verbose:
                print('Checking if Firefox local profile is fresh...')
            dst_folder = os.path.join(DEFAULT_USER_HOME_CACHE_PATH, 'firefox.profile')
            last_modified = datetime.fromtimestamp(os.path.getmtime(dst_folder))
            days_diff = (datetime.now() - last_modified).days
            if days_diff <= copy_threshold_days:
                if verbose:
                    print('Firefox local profile is fresh. Skipping the copy operation.')
                profile_folder = dst_folder
            else:
                if verbose:
                    print('Copying Firefox local profile into temporary folder.')
                if os.path.exists(dst_folder):
                    shutil.rmtree(dst_folder)
                shutil.copytree(src_folder, dst_folder, ignore=shutil.ignore_patterns('*parent.lock'))
                if verbose:
                    print('Firefox local profile copied into temporary folder.')
                profile_folder = dst_folder
        else:
            profile_folder = src_folder
    options = Options()
    if headless:
        options.add_argument("-headless")
    if profile_folder:
        options.add_argument('-profile')
        options.add_argument(profile_folder)
    if download_dir:
        options.set_preference('browser.download.folderList', 2)
        options.set_preference('browser.download.manager.showWhenStarting', False)
        options.set_preference('browser.download.dir', download_dir)
        options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')
    service = Service(geckodriver_path())
    driver = webdriver.Firefox(service=service, options=options)
    return driver
