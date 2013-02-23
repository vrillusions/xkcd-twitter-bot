#!/usr/bin/env python
# vim:ts=4:sw=4:ft=python:fileencoding=utf-8
"""Python Template.

This is a template for python.

"""


import sys
import os
import traceback
import cPickle
from ConfigParser import SafeConfigParser

import feedparser
sys.path.append("./lib/tweepy")
import tweepy


__version__ = '0.1.1'


def post_update(status):
    config = SafeConfigParser()
    if not config.read('config.ini'):
        print 'Could not read config file'
        sys.exit(1)
    consumer_key = config.get('twitter', 'consumer_key')
    consumer_secret = config.get('twitter', 'consumer_secret')
    access_token = config.get('twitter', 'access_token')
    access_token_secret = config.get('twitter', 'access_token_secret')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    try:
        api.update_status(status)
    except tweepy.error.TweepError, e:
        print "Error occurred while updating status:", e
        sys.exit(1)
    else:
        return True

        
def process_feed(url, cache_file, suffix = '#xkcd'):
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
        #print 'new post %s %s' % (rss['title'], rss['link'])
        post_update('%s %s %s' % (rss['title'], rss['link'], suffix))
        cPickle.dump(rss, open(cache_file, 'wb'), -1)
 

def main():
    """The main function."""
    process_feed('http://xkcd.com/rss.xml', 'cache-xkcd.dat', '#xkcd')
    process_feed('http://what-if.xkcd.com/feed.atom', 'cache-whatif.dat',
        '#xkcd #whatif')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, e:
        # Ctrl-c
        raise e
    except SystemExit, e:
        # sys.exit()
        raise e
    except Exception, e:
        print "ERROR, UNEXPECTED EXCEPTION"
        print str(e)
        traceback.print_exc()
        sys.exit(1)
    else:
        # Main function is done, exit cleanly
        sys.exit(0)


