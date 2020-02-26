from utils import log, utils

import requests
import time
from credentials import CLIENT_ID


def fetch_follows(user_id, limit=float('inf')):
    """
    Fetch all account following USER ID
    :param user_id: user_id
    :param limit: limit of follows to fetch
    :return: all followers from user_id
    """

    # Required variables
    all_follows = {}
    pagination = None
    ended = False

    while limit > len(all_follows):
        # Sleeping to avoid poll rate burn
        time.sleep(0.1)
        query = follows(user_id, pagination)

        # Storing next cursor
        try:
            pagination = query['_cursor']
        # Ending fetch if cursor wasn't provided (reached the end)
        except KeyError:
            ended = True
            break
        finally:
            # Adding follows to memory - Even after a break statement
            for follow in query['follows']:
                all_follows[follow['user']['_id']] = follow
            # Logging
            log.log(f"Total fetched: {len(all_follows)}/{'?' if not ended else len(all_follows)}")

    return all_follows


def follows(user_id, pagination):
    """
    Perform API follows endpoint request
    :param user_id: str or int
    :param pagination: str or None
    :return:
    """
    # Formatting query
    url = f"https://api.twitch.tv/v5/channels/{user_id}/follows?limit=100"

    # Adding Pagination information if required
    if pagination:
        pagination_query = '&cursor={}'.format(pagination)
        url += pagination_query

    # Returning parsed Json Response
    return requests.get(url, headers={'Client-ID': CLIENT_ID}).json()

def fetch_following(user_id, limit=float('inf')):
    """
    Fetch all channel followed by USER ID
    :param user_id: user_id to fetch follows from
    :param limit: limit of follows to fetch (in hundreds)
    :return: all followers from user_id
    """

    # Required variables
    all_follows = {}
    last_fetch = 0

    while limit > len(all_follows):
        # Sleeping to avoid poll rate burn
        time.sleep(0.1)

        # Performing Query
        query = following(user_id, offset=len(all_follows))

        # If no follows returned, stopping here
        if len(query['follows']) == 0:
            break

        # Adding follows to memory
        for follow in query['follows']:
            all_follows[follow['channel']['_id']] = follow

        # Leaving if no more  follows fetched this iteration
        if last_fetch == len(all_follows):
            break
        # Storing last fetch follow amount
        else:
            last_fetch = len(all_follows)

    return all_follows


def following(user_id, offset):
    """
    Perform API following endpoint request
    :param user_id: str or int
    :param offset: int
    :return:
    """
    # Formatting query
    url = f"https://api.twitch.tv/v5/users/{user_id}/follows/channels?limit=100&offset={offset}"
    return requests.get(url, headers={'Client-ID': CLIENT_ID}).json()

def users(user_id_list):
    """
    Perform API Users endpoint request
    :param user_id_list: list
    :return:
    """
    param = "id=" + '&id='.join(user_id_list)
    url = "https://api.twitch.tv/helix/users?{}".format(param)
    return requests.get(url, headers={"Client-ID": CLIENT_ID}).json()

def fetch_users(user_id_list):
    """
    Fetch all users info from users EndPoint
    :param user_id_list:
    :return:
    """
    chunks = [*utils.split_list(user_id_list, 100)]
    user_data = []

    progress = 0
    total = len(chunks)

    for chunk in chunks:
        time.sleep(1.5)
        query = users(chunk)
        for data in query['data']:
            user_data.append(data)

        progress += 1
        log.log(f"Fetching all Users data: {len(user_data)} [{round(progress / total * 100, 2)}%]")
    return user_data

def streams(user_id):
    """
    Gather stream data from V5 API Channels endpoint
    :param user_id:
    :return:
    """
    url = f"https://api.twitch.tv/v5/channels/{user_id}"
    return requests.get(url, headers={"Client-ID": CLIENT_ID}).json()


def get_user_id_by_login(login):
    """
    Uses Helix API to retrieve user_id by login
    :param login: name of the channel
    :return:
    """
    url = f"https://api.twitch.tv/helix/users?login={login}"
    return requests.get(url, headers={"Client-ID": CLIENT_ID}).json()