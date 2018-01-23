# coding: utf-8

# http://testpy.hatenablog.com/entry/2017/11/05/012906
# https://qiita.com/kenmatsu4/items/23768cbe32fe381d54a2

from requests_oauthlib import OAuth1Session
import json


CK = 'DtKRysI0UJUicH5lbKcDv0fH5'                             # Consumer Key
CS = 'LlQ8Vek2ARQ1RQUDoQYwItGjaiPvKPwDsWNxjv7W1Y12XxJQV4'         # Consumer Secret
AT = '3107466672-KpxPLFAINqHBhN175W2EVFcvLXb4ipBRcVHQPPb' # Access Token
AS = 'c6iwo2BfPeI6ArHTG5tfKHqXUm42sTeHIrTaJVWWd51SQ'         # Accesss Token Secert

api = OAuth1Session(CK, CS, AT, AS)


def search_tweet(api, params):
    url = 'https://api.twitter.com/1.1/search/tweets.json'
    req = api.get(url, params=params)

    result = []
    if req.status_code == 200:
        tweets = json.loads(req.text)
        result = tweets['statuses']
    else:
        print("ERROR!: %d" % req.status_code)
        result = None

    assert (len(result) > 0)

    return result


def output_tweets(result):
    for r in result:
        for k, v in r.items():
            if k in ['text', 'retweet_count', 'favorite_count', 'id', 'created_at']:
                print(k + ':')
                print(v)
                print('    ')
        print('-----------------------------------------------------------------')



params={
    'q': '#日産',
    'count': 20,
    'exclude': 'retweets'
}

result = search_tweet(api, params)
output_tweets(result)

