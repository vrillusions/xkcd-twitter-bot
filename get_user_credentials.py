#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get user oauth credentials.

Utility to help with getting the access token for a user

"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import sys
import logging

import tweepy
from six.moves.configparser import SafeConfigParser
from six.moves import input


def main():
    """The main function."""
    #log = logging.getLogger('main')
    config = SafeConfigParser()
    if not config.read('config.ini'):
        print('Could not read config file')
        return 1
    consumer_key = config.get('twitter', 'consumer_key')
    consumer_secret = config.get('twitter', 'consumer_secret')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError as exc:
        print('Error! Failed to get request token')
        print(exc)
        return 1
    print('Please go to the following url to authorize this app:')
    print("  {}\n".format(redirect_url))
    print('Enter the verifier code you see after authorizing app')
    verifier = input('Verifier: ')
    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        print('Error! Failed to get access token')
        return 1
    print('Enter these values in for access_token and access_token_secret')
    print('access_token: {}'.format(auth.access_token.key))
    print('access_token_secret: {}'.format(auth.access_token.secret))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
