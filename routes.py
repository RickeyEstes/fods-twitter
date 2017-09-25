from flask import Blueprint, jsonify, render_template, request
from pymongo import MongoClient

from bson.son import SON
from bson.json_util import dumps

import nltk
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import twitter_samples
from nltk.corpus import movie_reviews
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer

from shapely.geometry import shape, Point

import json
import gensim
import os
import pandas as pd
import random
import re
import string
import tarfile

import sys
reload(sys)
sys.setdefaultencoding('utf8')

routes = Blueprint('routes',__name__)

client = MongoClient('localhost:27017')
db = client.twitter
stop = set(stopwords.words('english'))
lemma = WordNetLemmatizer()

emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|"  # emoticons
    u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
    u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
    u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
    u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
    "+", flags=re.UNICODE)

# Load top hashtags with voter preference
top_hashtags = pd.read_csv('./static/data/top_hashtags.csv')
top_hashtags.columns = ['tweet_hashtag', 'hashtag_sentiment']
top_hashtags = top_hashtags.query('hashtag_sentiment == -1 or hashtag_sentiment == 1')
top_hashtags.reset_index(drop=True, inplace=True)
top_hashtags.head()

hillary_hashtags = set(top_hashtags[top_hashtags['hashtag_sentiment'] == -1]['tweet_hashtag'])
trump_hashtags = set(top_hashtags[top_hashtags['hashtag_sentiment'] == 1]['tweet_hashtag'])

def tweet_preference(tweet_hashtags):
    score = 0
    for hashtag in tweet_hashtags:
        if hashtag in hillary_hashtags:
            score -= 1
        elif hashtag in trump_hashtags:
            score += 1

    return score

# A function that extracts the hyperlinks from the tweet's content.
def extract_link(text):
    regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    match = re.search(regex, text)
    if match:
        return match.group()
    return ''

# # A function that extracts which words exist in a text based on a list of words to which we compare.
# def word_feats(words):
#         return dict([(word, True) for word in words])
#
# # Get the negative and positive reviews for movies
# negids = movie_reviews.fileids('neg')
# posids = movie_reviews.fileids('pos')
#
# # Find the features that most correspond to negative and positive reviews
# negfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'neg') for f in negids]
# posfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'pos') for f in posids]
#
# # We would only use 1500 instances to train on. The quarter of the reviews left is for testing purposes.
# negcutoff = len(negfeats)*3/4
# poscutoff = len(posfeats)*3/4
#
# # Construct the training dataset containing 50% positive reviews and 50% negative reviews
# trainfeats = negfeats+ posfeats[:poscutoff]
#
# # Construct the negative dataset containing 50% positive reviews and 50% negative reviews
# testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]
# # print testfeats[0]
# # Train a NaiveBayesClassifier
# classifier = NaiveBayesClassifier.train(trainfeats)
#
# # Test the trained classifier and display the most informative features.
# print 'train on %d instances, test on %d instances' % (len(trainfeats), len(testfeats))
# classifier.show_most_informative_features(32)
# print 'Classifier has been setup using movie reviews with an accuracy of:', nltk.classify.util.accuracy(classifier, testfeats)

@routes.route("/api/importStates", methods=["GET"])
def importStates():
    try:
        with open('./static/data/states.geojson', 'r+') as json_file:
            json_data = json.load(json_file)

            for (index, feature) in enumerate(json_data['features']):

                state = {}
                state["geometry"] = feature["geometry"]
                state["type"] = feature["type"]

                properties = {}
                properties["name"] = feature["properties"]["STATE_NAME"]
                properties["abbreviation"] = feature["properties"]["STATE_ABBR"]

                state["properties"] = properties

                db.states.insert_one(state)

            return jsonify(status='SUCCESS',message='Import succesful')

    except Exception,e:
        print e
        return jsonify(status='ERROR',message=str(e))

@routes.route("/api/getStates", methods=["GET"])
def getStates():
    try:
        states = []
        for state in db.states.find():
            state.pop('_id')
            states.append(state)

        return jsonify(result=states)

    except Exception,e:
        print e
        return jsonify(status='ERROR',message=str(e))

# @routes.route("/api/importMappedHashtags", methods=["GET"])
# def importMappedHashtags():
#     try:
#
#
#         return jsonify(status='SUCCESS',message="Done")
#
#     except Exception,e:
#         print e
#         return jsonify(status='ERROR',message=str(e))

@routes.route("/api/firstTweet",methods=['GET'])
def firstTweet():
    try:
        print "reading tweets"
        # Read twitter data
        tar = tarfile.open("./static/data/geotagged_tweets.tar.gz")
        raw_tweets = tar.extractfile("geotagged_tweets_20160812-0912.jsons")
        return raw_tweets.readline()

    except Exception,e:
        print e
        return jsonify(status='ERROR',message=str(e))

@routes.route("/api/importTweets",methods=['GET'])
def importTweets():
    try:
        # Read twitter data
        print "Reading Tweets file"
        tar = tarfile.open("./static/data/geotagged_tweets.tar.gz")
        raw_tweets = tar.extractfile("geotagged_tweets_20160812-0912.jsons")
        tweets = []

        # Load states
        states = list(db.states.find())

        for index, raw_tweet in enumerate(raw_tweets):

            # if index == 100:
            #     break

            if index % 1000 == 0:
                print index

            json_tweet = json.loads(raw_tweet)

            if json_tweet["lang"] == 'en' and ((json_tweet["place"] is not None and json_tweet["place"]["country_code"] == "US") or json_tweet["coordinates"] is not None) and json_tweet["user"]["lang"] == "en":

                # Extract raw data
                tweet = {}
                tweet["id"] = str(json_tweet["id"])
                tweet["date"] = json_tweet["created_at"]
                tweet["tetweeted"] = json_tweet["retweeted"]
                tweet["dirtyText"] = json_tweet["text"]

                # Extract hashtags
                tweet["hashtags"] = []
                for hashtag in json_tweet["entities"]["hashtags"]:
                    tweet["hashtags"].append(str(hashtag["text"]).lower())
                tweet["candidatePreference"] = tweet_preference(tweet["hashtags"])

                # Extract user mentions
                tweet["mentions"] = []
                for mention in json_tweet["entities"]["user_mentions"]:
                    tweet["mentions"].append(str(mention["screen_name"]))

                user = {}
                user["username"] = json_tweet["user"]["screen_name"]
                user["name"] = json_tweet["user"]["name"]
                user["followers"] = json_tweet["user"]["followers_count"]
                user["following"] = json_tweet["user"]["friends_count"]

                location = {}
                # Extract city if mentioned
                if json_tweet["place"] is not None and json_tweet["place"]["country_code"] == "US":
                    if json_tweet["place"]["place_type"] == "city":
                        location["city"] = json_tweet["place"]["name"]
                        location["state"] = json_tweet["place"]["full_name"].split(', ')[1]

                    if json_tweet["place"]["place_type"] == "neighborhood":
                        location["state"] = json_tweet["place"]["full_name"].split(', ')[1]

                    if json_tweet["place"]["place_type"] == "poi":
                        state = json_tweet["place"]["full_name"].split(', ')
                        if len(state) > 1:
                            location["state"] = state[1]

                    if json_tweet["place"]["place_type"] == "admin":
                        state = json_tweet["place"]["full_name"].split(', ')
                        if len(state) > 1:
                            response = list(db.states.find(
                                { "properties.name": state[0] }
                            ))
                            if len(response) > 1:
                                location["state"] = response[0]["properties"]["abbreviation"]

                        else:
                            location["state"] = state[0].split(' ')[1]

                # Extract coordinates if mentioned (use the coordinates field for correct x,y)
                if json_tweet["coordinates"] is not None:
                    location["coordinates"] = {}
                    point = Point(json_tweet["coordinates"]["coordinates"][0], json_tweet["coordinates"]["coordinates"][1])

                    for state in states:
                        polygon = shape(state["geometry"])
                        if polygon.contains(point):
                            # location["state"] = state["properties"]["name"]
                            location["coordinates"] = json_tweet["coordinates"]

                # Extract link and clean up
                link = extract_link(json_tweet["text"])
                sentiment_text = json_tweet["text"]
                sentiment_text = re.sub(r"http\S+", "", sentiment_text)

                # Clean user mentions
                sentiment_text = re.sub(r"@\S+", "", sentiment_text)

                # Clean hashtags
                sentiment_text = re.sub(r"#\S+", "", sentiment_text)

                # Clean ampersands
                sentiment_text = re.sub(r"&amp;", "", sentiment_text)

                # Clean special characters
                sentiment_text = re.sub("[^A-Za-z]+", " ", sentiment_text)

                # Convert to lowercase
                sentiment_text = sentiment_text.lower()

                # Add cleaned text
                tweet["sentText"] = sentiment_text

                topic_text = sentiment_text
                topic_text = " ".join([i for i in topic_text.lower().split() if i not in stop])
                topic_text = " ".join(lemma.lemmatize(word) for word in topic_text.split())
                topic_text.split()
                tweet["topicText"] = topic_text

                tweet["user"] = user
                tweet["location"] = location

                # # Get sentiment
                # tweet["sentiment"] = classifier.classify(word_feats(json_tweet["text"]))

                if 'coordinates' in tweet["location"] and tweet["location"]["coordinates"] != {}:
                    db.tweets.insert_one(tweet)
                if not 'coordinates' in tweet["location"]:
                    db.tweets.insert_one(tweet)

                tweets.append(tweet)

        #         json_tweet["text"] = tokenizer.tokenize(json_tweet["text"].lower())
        #         json_tweet["text"] = [word for word in json_tweet["text"] if word not in stopwords.words('english')]
        #         json_tweet["text"] = ' '.join(json_tweet["text"])
        # #
        #         for output_line in run_command(['java', '-jar', 'C:\SentiStrength\SentiStrengthCom.jar', 'sentidata', 'C:/SentiStrength/SentStrength_Data/', 'text', json_tweet["text"], 'binary']):
        #             result = output_line.split()
        #             json_tweet["text"] = tokenizer.tokenize(json_tweet["text"].lower())
        #
        #             if result[2] == '1':
        #                 tweets.append(tuple((json_tweet["text"], 'positive')))
        #             else:
        #                 tweets.append(tuple((json_tweet["text"], 'negative')))
        #
        #         for hashtag in json_tweet["entities"]["hashtags"]:
        #             hashtags.append(str(hashtag["text"]))

        return jsonify(status='OK',message="Completed Tweet import")

    except Exception,e:
        print e
        return jsonify(status='ERROR',message=json_tweet)

@routes.route("/api/getTweets",methods=['GET'])
def getTweets():
    try:
        tweets = db.tweets.find().limit(10000)

        tweetList = []
        for tweet in tweets:
            tweetItem = (word_feats(json.dumps(tweet["text"])), tweet["sentiment"])
            print tweetItem
            tweetList.append(tweetItem)

        accuracy = nltk.classify.util.accuracy(classifier, tweetList)
        return accuracy

    except Exception,e:
        return str(e)

@routes.route("/api/getHashtags",methods=['GET'])
def getAllHashtags():
    try:
        tweets = list(db.tweets.aggregate([
            { "$unwind": "$hashtags" },
            { "$group": {
                "_id": "$hashtags",
                "count": { "$sum": 1 }
            }},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]))

        return jsonify(result=tweets[:20])

    except Exception,e:
        return str(e)

@routes.route("/api/getHashtags/<state>",methods=['GET'])
def getStateHashtags(state):
    try:
        state = list(db.states.find(
            { "properties.abbreviation": state }
        ))

        state = state[0]
        tweets = list(db.tweets.aggregate([
            { "$match" :
                { "$or": [
                    { "location.state" : state["properties"]["abbreviation"] },
                    { "location.coordinates" : { "$geoWithin": { "$geometry": state["geometry"] } } }
                ]}
            },
            { "$unwind": "$hashtags" },
            { "$group": {
                "_id": "$hashtags",
                "count": { "$sum": 1 }
            }},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]))

        return jsonify(result=tweets[:20])

    except Exception,e:
        return str(e)

@routes.route("/api/getPreference",methods=['GET'])
def getPreference():
    try:
        tweets = list(db.tweets.aggregate([
            { "$unwind": "$candidatePreference" },
            { "$group": {
                "_id": "$candidatePreference",
                "count": { "$sum": 1 }
            }},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]))

        return jsonify(result=tweets[:20])

    except Exception,e:
        return str(e)

@routes.route("/api/getPreference/<state>",methods=['GET'])
def getStatePreference(state):
    try:
        state = list(db.states.find(
            { "properties.abbreviation": state }
        ))

        state = state[0]
        tweets = list(db.tweets.aggregate([
            { "$match" :
                { "$or": [
                    { "location.state" : state["properties"]["abbreviation"] },
                    { "location.coordinates" : { "$geoWithin": { "$geometry": state["geometry"] } } }
                ]}
            },
            { "$unwind": "$candidatePreference" },
            { "$group": {
                "_id": "$candidatePreference",
                "count": { "$sum": 1 }
            }},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]))

        return jsonify(result=tweets[:20])

    except Exception,e:
        return str(e)

@routes.route("/api/getTopics/<state>",methods=['GET'])
def getStateTopics(state):
    try:
        state = list(db.states.find(
            { "properties.abbreviation": state }
        ))

        state = state[0]
        tweetList = list(db.tweets.find(
            { "location.state": state["properties"]["abbreviation"] }
        ))

        print len(tweetList)

        tweets = []

        rnd = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

        for tweet in tweetList:
            if tweet["topicText"] != "":
                split = tweet["topicText"].split(" ")
                tweets.append(split)

        # Creating the term dictionary of our courpus, where every unique term is assigned an index
        id2word = gensim.corpora.Dictionary(tweets)

        # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
        raw_corpus = [id2word.doc2bow(tweet) for tweet in tweets]
        gensim.corpora.MmCorpus.serialize('./static/data/tmp/' + rnd + '.mm', raw_corpus)
        corpus = gensim.corpora.MmCorpus('./static/data/tmp/' + rnd + '.mm')
        # ldamodel = gensim.models.ldamodel.LdaModel(corpus=corpus, id2word=id2word, num_topics=5, update_every=1, chunksize=10000, passes=1)
        # lda = ldamodel.print_topics(num_topics=5, num_words=5)

        os.remove("./static/data/tmp/" + rnd + ".mm")
        os.remove("./static/data/tmp/" + rnd + ".mm.index")

        # Creating the object for LDA model using gensim library
        Lda = gensim.models.ldamodel.LdaModel(raw_corpus, num_topics=5, id2word = id2word, passes=1)
        lda = ldamodel.print_topics(num_topics=5, num_words=5)


        return jsonify(result=lda)

    except Exception,e:
        return jsonify(status='ERROR',message=str(e))

@routes.route("/api/getTweets/<state>",methods=['GET'])
def getStateTweets(state):
    try:
        tweets = list(db.tweets.find(
            { "location.state": state }
        ))

        text = []

        text_file = open(state + ".txt", "w")
        for tweet in tweets:
            stripped_text = tweet["text"].rstrip()
            text.append(stripped_text)
            stripped_text += "\n"
            text_file.write(stripped_text)
        text_file.close()

        hashtags_file = open(state + "hash.txt", "w")
        for tweet in tweets:
            if str(tweet["hashtags"]) != '[]':
                hashtags_file.write(str(tweet["hashtags"]) + "\n")

        hashtags_file.close()

        return jsonify(result=text)

    except Exception,e:
        return jsonify(status='ERROR',message=str(e))
