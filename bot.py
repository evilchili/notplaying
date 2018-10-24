from mastodon import Mastodon
import random
import html
import re

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

def main():
    mastodon = Mastodon(
        access_token = '116b8605df66ecd014b864935a94ca55341fc1bd81574418e86d417720075372',
        api_base_url = 'https://botsin.space/'
    )
    toots = mastodon.timeline_hashtag('nowplaying', limit=40)
    (artists, titles) = zip(*get_supergroup(toots))
    mastodon.toot(formatted_toot(remix(artists, titles)))


if __name__ == '__main__':
    main()
