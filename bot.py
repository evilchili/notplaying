from mastodon import Mastodon
import os
import random
import html
import re
import time
import json
import logging

logging.getLogger().setLevel(logging.DEBUG)

account_id = 9406

np_pattern = re.compile('#<span>bot</span>.+<p>(.+)\s-\s"([^"]+)"</p>')

def formatted_toot(title):
    """
    Return a formatted string suitable for tooting.

    Args:
        title (str): A song title to toot

    Returns:
        str: A formatted string ready for tooting
    """
    return f"""
🎶 #notplaying #np #fediplay #bot 🎶

{title}
"""

def remix(artists, titles):
    """
    Imagine a new song by combining artists and song titles.

    Args:
        artists (list): the list of artists to use
        titles (list): the list of song titles to use

    Returns:
        str: The next deep banger
    """
    return '{} vs {} - {} {}'.format(*artists, *titles)

def get_random_toot(toots):
    """
    Select a random toot from a list of toots and return the HTML-decoded content.

    Args:
        toots (list): a list of dictionaries

    Returns:
        str: the HTML-decoded content of a toot
    """
    return html.unescape(random.choice(toots)['content'])


def get_supergroup(now_playing_toots):
    """
    Randomly select artists and song titles from the #nowplaying hashtag on mastodon

    Args:
        now_playing_toots (list): A list of dictionaries including the 'content' key

    Returns:
        list: A list of (artist name string, song title string) tuples
    """
    supergroup = []
    while len(supergroup) != 2:
        m = np_pattern.findall(get_random_toot(now_playing_toots))
        if m and m[0] not in now_playing_toots:
            if m[0][0] not in [x[0] for x in supergroup]:
                supergroup.append(m[0])
    return supergroup

def write_cache(toots):
    with open('toot.cache', 'w') as f:
        json.dump(toots, f, indent=4, default=str)

def get_cached_toots():
    try:
        with open('toot.cache') as f:
            return json.load(f)
    except:
        return []

def max_id(toots):
    return min([t['id'] for t in toots]) if toots else None

def get_historical_toots(client):
    count = 0
    while count < 10 and len(toots) < 1000:
        toots += client.account_statuses(id=account_id, limit=100, max_id=max_id(toots))
        count += 1
        time.sleep(0.2)
    return toots

def get_new_toots(client, since_id):
    # OHNO: lossy, if there have been more than 100 toots since since_id
    logging.info("Refreshing toot list...")
    return client.account_statuses(id=account_id, limit=100, since_id=since_id)

def main():
    mastodon = Mastodon(
        access_token = os.environ.get('MASTODON_TOKEN'),
        api_base_url = 'https://botsin.space/'
    )
    toots = get_cached_toots() or get_historical_toots(mastodon)
    toots += get_new_toots(mastodon, max_id(toots))
    write_cache(toots)

    (artists, titles) = zip(*get_supergroup(toots))
    new_toot = formatted_toot(remix(artists, titles))
    logging.debug(new_toot)
    mastodon.toot(new_toot)


if __name__ == '__main__':
    main()
