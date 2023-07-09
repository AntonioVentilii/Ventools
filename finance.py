"""
Provides utility functions related to finance.

Author: Antonio Ventilii
"""

import requests

user_agent_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.124 Safari/537.36'
}


def cross(c1: str, c2: str, sep: str = '') -> str:
    """
    Returns the cross currency pair given currency 1 and currency 2 according to market convention.

    Args:
        c1 (str): Currency 1.
        c2 (str): Currency 2.
        sep (str, optional): Separator for the cross currency pair. Defaults to ''.

    Returns:
        str: The cross currency pair.
    """
    priority = {
        'xau': 1,
        'xag': 2,
        'eur': 3,
        'gbp': 4,
        'aud': 5,
        'nzd': 6,
        'usd': 7,
        'chf': 1e6
    }
    if sep is None:
        sep = ''
    p1 = priority.get(c1.lower(), len(priority))
    p2 = priority.get(c2.lower(), len(priority))
    if p1 <= p2:
        c = c1 + sep + c2
    else:
        c = c2 + sep + c1
    return c


def fx_rate(from_curr: str, to_curr: str, proxies: dict[str, str] = None) -> float:
    """
    Retrieve the foreign exchange rate between two currencies using Yahoo Finance API.

    Args:
        from_curr (str): The currency code for the base currency.
        to_curr (str): The currency code for the target currency.

    Returns:
        float: The exchange rate from the base currency to the target currency.

    Raises:
        KeyError: If the JSON response from Yahoo Finance API does not contain the expected data.
    """

    mapper = {
        'cnh': 'cny'
    }
    from_curr = mapper.get(from_curr.lower(), from_curr)
    to_curr = mapper.get(to_curr.lower(), to_curr)

    if from_curr.lower() == to_curr.lower():
        return 1  # Return 1 if the base and target currencies are the same

    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{from_curr}{to_curr}=X'
    r = requests.get(url, proxies=proxies, headers=user_agent_headers)

    ret = r.json()['chart']['result'][0]['meta']['regularMarketPrice']

    return ret
