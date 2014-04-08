#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Update twitter from an rss feed.

Parse an rss feed for new entries and post them to twitter.

TODO: no maintenance is done on cache so it can get large over time

Environment Variables
    LOGLEVEL: overrides the level specified here. Default is warning
        choices: DEBUG, INFO, WARNING, ERROR, or CRITICAL

"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import logging
import os
import sys
from datetime import datetime
from ConfigParser import SafeConfigParser
from optparse import OptionParser
try:
    import cPickle as pickle
except ImportError:
    import pickle

import feedparser
import tweepy


__version__ = '0.5.0-dev'


def _parse_opts(argv=None):
    """Parse the command line options.

    :param list argv: List of arguments to process. If not provided then will
        use optparse default
    :return: options,args where options is the list of specified options that
        were parsed and args is whatever arguments are left after parsing all
        options.

    """
    parser = OptionParser(version='%prog {}'.format(__version__))
    parser.set_defaults(verbose=False)
    parser.add_option('-c', '--config', dest='config', metavar='FILE',
        help='use config FILE (default: %default)', default='config.ini')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='be more verbose (default is no)')
    (options, args) = parser.parse_args(argv)
    return options, args


class TwitterBot(object):
    def __init__(self, consumer_key, consumer_secret):
        """Class to handle posting to twitter.

        Intentionally the access_token and access_token_secret are not set at
        initialization. This way it's possible to post different feeds to
        different users.

        :param string consumer_key: The application api key
        :param string consumer_secret: The application api secret

        """
        self.log = logging.getLogger('main.TwitterBot')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = None
        self.access_token_secret = None
        self.cache_file = 'cache.dat'
        self._cache = self._load_cache()
        self.log.debug('cache: {}'.format(self._cache))

    def _load_cache(self):
        """Loads cache file.

        :return: either existing cache or blank dict if new

        """
        self.log.debug('enter _load_cache()')
        try:
            cache = pickle.load(open(self.cache_file, 'rb'))
        except IOError as exc:
            if exc.errno == 2:
                # 2 is file not found continue on
                self.log.warning('Cache file not found, creating new cache')
                cache = {}
            else:
                raise
        return cache

    def _save_cache(self):
        """Saves cache .

        :return: True on success

        """
        self.log.debug('enter _save_cache()')
        with open(self.cache_file, 'wb') as fh:
            pickle.dump(self._cache, fh, -1)
        return True

    def post_update(self, status):
        """Posts update to twitter.

        :param string status: Status text to post
        :return: Returns True on success

        """
        self.log.debug('enter post_update()')
        self.log.debug('status: {}'.format(status))
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth)
        try:
            api.update_status(status)
        except tweepy.error.TweepError as exc:
            self.log.critical('Error occurred while updating status: {}'.format(exc))
            sys.exit(1)
        else:
            return True

    def process_feed(self, url, suffix = '#xkcd'):
        """Process the given feed for new items.

        :param string url: URL to RSS feed
        :param string suffix: Tags to append to status

        """
        self.log.debug('enter process_feed()')
        self.log.debug('url: {}'.format(url))
        self.log.debug('suffix: {}'.format(suffix))
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry['id'] not in self._cache:
                self.log.debug('{} not cached, posting'.format(entry['id']))
                post = ' '.join((entry['title'], entry['link'], suffix))
                self.log.info('new post: {}'.format(post))
                self.post_update(post)
                self._cache[entry['id']] = datetime.utcnow().isoformat()
                # Save cache after each successful post (may be a little
                # excessive)
                self._save_cache()
            else:
                self.log.debug('{} exists in cache, skipping'
                        .format(entry['id']))


def main(argv=None):
    """The main function.

    :param list argv: List of arguments passed to command line. Default is None,
        which then will translate to having it set to sys.argv.

    :return: Optionally returns a numeric exit code. If not given then will
        default to 0.
    :rtype: int

    """
    loglevel = getattr(logging, os.getenv('LOGLEVEL', 'WARNING').upper())
    logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=loglevel, format=logformat)
    log = logging.getLogger('main')
    if argv is None:
        argv = sys.argv
    options = _parse_opts(argv)[0]
    if options.verbose:
        log.setLevel(logging.DEBUG)
    config = SafeConfigParser()
    if not config.read(options.config):
        log.critical('Could not read config file')
        sys.exit(1)
    consumer_key = config.get('twitter', 'consumer_key')
    consumer_secret = config.get('twitter', 'consumer_secret')
    access_token = config.get('twitter', 'access_token')
    access_token_secret = config.get('twitter', 'access_token_secret')
    twitterbot = TwitterBot(consumer_key, consumer_secret)
    twitterbot.access_token = access_token
    twitterbot.access_token_secret = access_token_secret
    twitterbot.process_feed('http://xkcd.com/rss.xml', '#xkcd')
    twitterbot.process_feed('http://what-if.xkcd.com/feed.atom', '#xkcd #whatif')


if __name__ == "__main__":
    sys.exit(main())
