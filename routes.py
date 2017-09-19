from flask import Blueprint, jsonify, render_template, request
from pymongo import MongoClient

import json
import tarfile

routes = Blueprint('routes',__name__)

client = MongoClient('localhost:27017')
db = client.twitter

# @routes.route("/api/addTweet",methods=['POST'])
# def addTweet():
#     try:
#
#         if not request.json:
#             abort(400)
#
#         json_data       = request.json
#
#         userName        = json_data['username']
#         text            = json_data['text']
#
#         print json_data
#
#         db.tweets.insert_one({
#             'username':userName,
#             'text': text
#             })
#         return jsonify(status='OK',message='inserted successfully')
#
#     except Exception,e:
#         print e
#         return jsonify(status='ERROR',message=str(e))

@routes.route("/api/importTweets",methods=['GET'])
def importTweets():
    try:
        # Read twitter data
        tar = tarfile.open("./static/data/geotagged_tweets.tar.gz")
        raw_tweets = tar.extractfile("geotagged_tweets_20160812-0912.jsons")
        line = raw_tweets.readline()

        print line

        return jsonify(status='OK',message=line)

    except Exception,e:
        print e
        return jsonify(status='ERROR',message=str(e))

@routes.route("/api/getTweets",methods=['POST'])
def getTweets():
    try:
        tweets = db.tweets.find()

        tweetList = []
        for tweet in tweets:
            print tweet
            tweetItem = {
                    'username':tweet['username'],
                    'text':tweet['text'],
                    }
            tweetList.append(tweetItem)
    except Exception,e:
        return str(e)
    return json.dumps(tweetList)
