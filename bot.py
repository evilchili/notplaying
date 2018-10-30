from mastodon import Mastodon
import os
import random
import html
import re
import time
import json
import random
import logging

logging.getLogger().setLevel(logging.DEBUG)
np_pattern = re.compile('#<span>bot</span>.+<p>(.+)\s-\s"([^"]+)"</p>')
paren_pattern = re.compile('\s+(\(.+?\))')

ACCOUNT_ID = 9406
MAXIMUM_HISTORICAL_TOOTS = 5000
CACHE_FILE = 'toot.cache'


class Producer:
    """
    Only the dopest, most fire producers to light this joint, by which I mean generate a randomized
    artist and song title from two or more sets of artists and titles.
    """
    def __init__(self, artists, titles):
        """
        Constructor.
        
        Args:
            artists (list): List of artist names to remix
            titles (list): List of title names to remix
        """
        self.artists = artists
        self.titles = titles
        self.suffixes = [
            "(Studio Version)",
            "(Live)",
            "(Remix)",
            "(Radio Edit)",
            "(7-inch)",
            "(12-inch)",
            "(Dance Mix)",
            "(Club Mix)",
            "(Instrumental)",
            "(Acapella)",
            "(Doo-Wop Version)",
            "(Electric Version)",
            "(Acoustic Verison)",
            "(Alternate Take)",
            "(False Start)",
            "(Redux)",
        ]
        self.extract_suffixes()

    def remix(self):
        """
        Generate a randomized song.
        """
        title = random.choice(self.types)()
        if random.choice([True, False]):
            return title
        if not self.suffixes:
            return title
        return '{} {}'.format(title, random.choice(self.suffixes))

    def extract_suffixes(self):
        """
        Remove the trailing (...) strings from our song titles so we can randomly assign a new one.
        """
        titles = []
        for t in self.titles:
            self.suffixes += paren_pattern.findall(t)
            titles.append(paren_pattern.sub('', t))
        self.titles = titles

    def mix_mashup(self):
        return '{} vs {} - {} {}'.format(
            *random.sample(self.artists, 2),
            *random.sample(self.titles, 2)
        )

    def mix_duet(self):
        return '{} feat. {} - {}'.format(
            *random.sample(self.artists, 2),
            random.choice(self.titles)
        )

    def mix_cover(self):
        index = random.sample([0, 1], 2)
        return '{} - {}'.format(self.artists[index[0]], self.titles[index[1]])

    @property
    def types(self):
        """
        The list of methods on the current instance that define remix times.
        """
        return [getattr(self, method) for method in dir(self) if method.startswith('mix_')]


class Tooter:
    """
    Cache toots from the toot-lab and post new ones to the @notplaying account.
    """
    def __init__(self, token, url):
        self.client = Mastodon(access_token=token, api_base_url=url)
        self._toot_cache = []
        self.toot_format = '\n'.join([
            '🎶 #notplaying #np #fediplay #bot 🎶',
            '',
            '{title}'
        ])

    def toot(self, title):
        self.client.toot(self.formatted_toot(title))

    def formatted_toot(self, title):
        """
        Return a formatted string suitable for tooting.

        Args:
            title (str): A song title to toot

        Returns:
            str: A formatted string ready for tooting
        """
        return self.toot_format.format(title=title)

    def get_random_toot(self):
        """
        Select a random toot from a list of toots and return the HTML-decoded content.

        Args:
            toots (list): a list of dictionaries

        Returns:
            str: the HTML-decoded content of a toot
        """
        return html.unescape(random.choice(self.toots)['content'])


    def get_supergroup(self):
        """
        Randomly select artists and song titles from the toot cache

        Returns:
            list: A list of (artist name string, song title string) tuples
        """
        supergroup = []
        while len(supergroup) != 2:
            m = np_pattern.findall(self.get_random_toot())
            if m and m[0] not in self.toots:
                if m[0][0] not in [x[0] for x in supergroup]:
                    supergroup.append(m[0])
        return zip(*supergroup)

    def _write_cache(self):
        """
        Write the toot cache to disk.
        """
        with open(CACHE_FILE, 'w') as f:
            logging.debug("Writing cache...")
            json.dump(self._toot_cache, f, indent=4, default=str)

    def _load_cache(self):
        """
        Load the toot cache from disk.
        """
        self._toot_cache = []
        try:
            logging.debug("Loading toot cache...")
            with open(CACHE_FILE) as f:
                self._toot_cache = json.load(f)
        except:
            logging.debug("Nothing cached.")

    def _backfill_cache(self):
        """
        If the cache is light, backfill it from live data.
        """
        while len(self._toot_cache) < MAXIMUM_HISTORICAL_TOOTS:
            self._toot_cache += self.client.account_statuses(
                id=ACCOUNT_ID,
                limit=100,
                max_id=self.oldest_toot
            )
            logging.debug("Refreshing Cache: {} toots".format(len(self._toot_cache)))
            time.sleep(0.2)

    def _refresh_cache(self):
        """
        Get toots tooted since the latest cached toot.
        """
        # OHNO: lossy, if there have been more than 100 toots since since_id
        logging.info("Refreshing toot list...")
        self._toot_cache += self.client.account_statuses(
            id=ACCOUNT_ID,
            limit=100,
            since_id=self.newest_toot
        )

    @property
    def newest_toot(self):
        return max([t['id'] for t in self._toot_cache]) if self._toot_cache else None

    @property
    def oldest_toot(self):
        return min([t['id'] for t in self._toot_cache]) if self._toot_cache else None

    @property
    def toots(self):
        if not self._toot_cache:
            self._load_cache()
            self._backfill_cache()
            self._refresh_cache()
            self._write_cache()
        return self._toot_cache


def main():
    tooter = Tooter(
        token=os.environ.get('MASTODON_TOKEN'),
        url='https://botsin.space/'
    )

    (artists, titles) = tooter.get_supergroup()
    song_title = Producer(list(artists), list(titles)).remix()
    tooter.toot(song_title)

    #for i in range(10):
    #    (artists, titles) = tooter.get_supergroup()
    #    new_toot = Producer(list(artists), list(titles)).remix()
    #    logging.debug(new_toot)


if __name__ == '__main__':
    main()
