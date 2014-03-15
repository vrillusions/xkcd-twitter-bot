#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Update twitter from an rss feed.

Parse an rss feed for new entries and post them to twitter.

Environment Variables
    LOGLEVEL: overrides the level specified here. Default is warning

"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import logging
import os
import sys
import cPickle
from ConfigParser import SafeConfigParser

import feedparser
sys.path.append("./lib/tweepy")
import tweepy


__version__ = '0.3.0'


# Logger config
# DEBUG, INFO, WARNING, ERROR, or CRITICAL
# This will set log level from the environment variable LOGLEVEL or default
# to warning. You can also just hardcode the error if this is simple.
_LOGLEVEL = getattr(logging, os.getenv('LOGLEVEL', 'WARNING').upper())
_LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=_LOGLEVEL, format=_LOGFORMAT)


def post_update(status):
    log = logging.getLogger('post_update')
    log.debug('status: {}'.format(status))
    config = SafeConfigParser()
    if not config.read('config.ini'):
        log.critical('Could not read config file')
        sys.exit(1)
    consumer_key = config.get('twitter', 'consumer_key')
    consumer_secret = config.get('twitter', 'consumer_secret')
    access_token = config.get('twitter', 'access_token')
    access_token_secret = config.get('twitter', 'access_token_secret')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, secure=True)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    try:
        api.update_status(status)
    except tweepy.error.TweepError as exc:
        log.critical('Error occurred while updating status: {}'.format(exc))
        sys.exit(1)
    else:
        return True


def process_feed(url, cache_file, suffix = '#xkcd'):
    log = logging.getLogger('process_feed')
    log.debug('url: {}'.format(url))
    log.debug('cache_file: {}'.format(cache_file))
    log.debug('suffix: {}'.format(suffix))
    feed = feedparser.parse(url)
    # lots of scary warnings about possible security risk using this method
    # but for local use I'd rather do this than a try-catch with open()
    if not os.path.isfile(cache_file):
        # make a blank cache file
        cPickle.dump({'id': None}, open(cache_file, 'wb'), -1)
    cache = cPickle.load(open(cache_file))
    rss = {}
    rss['id'] = feed['entries'][0]['id']
    rss['link'] = feed['entries'][0]['link']
    rss['title'] = feed['entries'][0]['title']
    rss['summary'] = feed['entries'][0]['summary']
    # compare with cache
    if cache['id'] != rss['id']:
        post = '{} {} {}'.format(rss['title'], rss['link'], suffix)
        log.info('new post: {}'.format(post))
        post_update(post)
        cPickle.dump(rss, open(cache_file, 'wb'), -1)


def main():
    """The main function."""
    process_feed('http://xkcd.com/rss.xml', 'cache-xkcd.dat', '#xkcd')
    process_feed('http://what-if.xkcd.com/feed.atom', 'cache-whatif.dat',
        '#xkcd #whatif')


if __name__ == "__main__":
    sys.exit(main())
