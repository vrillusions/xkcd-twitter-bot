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
import logging.config
import os
import sys
from datetime import datetime, timedelta
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
        self.log = logging.getLogger('TwitterBot')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = None
        self.access_token_secret = None
        self.cache_file = 'cache.dat'
        self._cache = self._load_cache()
        # TEMPORARY, can remove next version
        self._convert_dates()
        self.log.debug('cache: %s', self._cache)

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

    def _convert_dates(self):
        # TEMPORARY: convert time strings to datetime objects
        # Before v0.5.0 the date was a string in iso8601 format which
        # complicates things when cleaning up the cache. This converts those
        # dates back to datetime objects.
        self.log.debug('enter _convert_dates()')
        date_format = '%Y-%m-%dT%H:%M:%S.%f'
        for url, cache_date in self._cache.iteritems():
            if isinstance(cache_date, basestring):
                self.log.debug('Convert %s:%s', url, cache_date)
                cache_date_dt = datetime.strptime(cache_date, date_format)
                self._cache[url] = cache_date_dt
        self._save_cache()

    def post_update(self, status):
        """Posts update to twitter.

        :param string status: Status text to post
        :return: Returns True on success

        """
        self.log.debug('enter post_update()')
        self.log.debug('status: %s', status)
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth)
        try:
            api.update_status(status)
        except tweepy.error.TweepError as exc:
            self.log.critical('could not update status: %s', exc, exc_info=True)
            sys.exit(1)
        else:
            return True

    def process_feed(self, url, suffix='#xkcd'):
        """Process the given feed for new items.

        :param string url: URL to RSS feed
        :param string suffix: Tags to append to status

        """
        self.log.debug('enter process_feed()')
        self.log.debug('url: %s', url)
        self.log.debug('suffix: %s', suffix)
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry['id'] not in self._cache:
                self.log.debug('%s not cached, posting', entry['id'])
                post = ' '.join((entry['title'], entry['link'], suffix))
                self.log.info('new post: %s', post)
                self.post_update(post)
            else:
                self.log.info('%s exists in cache, skipping', entry['id'])
            # Always want to update the date in case an entry is stickied to the
            # top of the list
            self._cache[entry['id']] = datetime.utcnow()
            # Save cache after each successful post (may be a little excessive)
            self._save_cache()

    def cleanup_cache(self, days=60):
        """Removes old entries from cache.

        :param int days: Remove items last seen this many days ago

        """
        self.log.debug('enter cleanup_cache(%s)', days)
        prune_date = datetime.utcnow() - timedelta(days=days)
        # Can't delete items from cache as we iterate through it, so need copy.
        cache_copy = self._cache.copy()
        for url, cache_date in cache_copy.iteritems():
            if cache_date < prune_date:
                self.log.info('removing %s (last seen: %s)', url, cache_date)
                del self._cache[url]
        self._save_cache()


def main(argv=None):
    """The main function.

    :param list argv: List of arguments passed to command line. Default is None,
        which then will translate to having it set to sys.argv.

    :return: Optionally returns a numeric exit code. If not given then will
        default to 0.
    :rtype: int

    """
    log = logging.getLogger()
    if argv is None:
        argv = sys.argv
    options = _parse_opts(argv)[0]
    if options.verbose:
        # BUG: setlevel doesn't work now I'm using fileconfig
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
    twitterbot.cleanup_cache()
    log.info('finished')


if __name__ == "__main__":
    logging.config.fileConfig('logging.ini')
    sys.exit(main())
