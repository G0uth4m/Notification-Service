from flask import render_template, jsonify, Response, request, url_for
from app import app, mongo
from app.tasks import send_web_push, publish
import requests
from datetime import datetime


@app.route('/')
def index():
    return render_template('index.html')

"""
Send public key of the server to the endpoint device
"""
@app.route('/api/v1/vapid/public/key')
def get_vapid_public_key():
    pub_key = app.config['VAPID_PUBLIC_KEY']
    if pub_key is None:
        return Response(status=404)

    return jsonify({'public_key': pub_key})


"""
Create a topic. In our case subscribe industry for notifications
"""
@app.route('/api/v1/topics/', methods=["POST"])
def create_topic():
    if not request.json or not request.json.get('topic'):
        return Response(status=400)

    topic_name = request.json.get('topic')
    description = request.json.get('description')
    if description is None:
        description = ""

    collection = mongo.db.topics
    if collection.find_one({'topic': topic_name}):
        return Response(status=400)
    
    collection.insert_one({'topic': topic_name, 'description': description, 'subscribers': [], 'notifications': []})
    # TODO : Monitor the added industry using database triggers
    return Response(status=201)

"""
List all the topics created. In our case list all industries
"""
@app.route('/api/v1/topics/list')
def list_topics():
    collection = mongo.db.topics
    res = list(collection.find({}, {'_id': 0, 'topic': 1}))
    res = [i['topic'] for i in res]
    if res == []:
        return Response(status=204)
    return jsonify(res)

"""
Delete a topic. In our case unsubscribe industry for notifications
"""
@app.route('/api/v1/topics/<topic>', methods=["DELETE"])
def remove_topic(topic):
    collection = mongo.db.topics

    res = collection.remove({'topic': topic})
    if res['n'] == 0:
        return Response(status=400)
    
    return Response(status=200)

"""
Subscribe an endpoint device to a topic
"""
@app.route('/api/v1/topics/subscribe', methods=["POST"])
def subscribe_to_topic():
    if not request.json or not request.json.get('topic') or not request.json.get('token'):
        return Response(status=400)
    
    topic_name = request.json.get('topic')
    token = request.json.get('token')

    topics_collection = mongo.db.topics

    res = topics_collection.update_one({'topic': topic_name}, {'$addToSet': {'subscribers': token}})
    if res.raw_result['n'] == 0:
        return Response(status=400)

    return Response(status=200)

""""
Unsubscribe an endpoint device from a topic
"""
@app.route('/api/v1/topics/unsubscribe', methods=["POST"])
def unsubscribe_from_topic():
    if not request.json or not request.json.get('token') or not request.json.get('topic'):
        return Response(status=400)
    
    token = request.json.get('token')
    topic_name = request.json.get('topic')

    collection = mongo.db.topics
    
    res = collection.update_one({'topic': topic_name}, {'$pull': {'subscribers': token}})
    if res.raw_result['n'] == 0 or res.raw_result['nModified'] == 0:
        return Response(status=400)

    return Response(status=200)

"""
Given the endpoint subscription token and the notification message. Send
push notification to that endpoint
"""
@app.route('/api/v1/notifications/push', methods=["POST"])
def push_notifications():
    if not request.json or not request.json.get('token') or not request.json.get('notification'):
        return Response(status=400)
    
    token = request.json.get('token')
    notification = request.json.get('notification')

    send_web_push.queue(token, notification)
    
    return Response(status=200)

"""
List notifications received by a topic (in our case industry)
"""
@app.route('/api/v1/notifications/list')
def list_notifications_of_topic():
    if not request.args.get('topic') or not request.args.get('start') or not request.args.get('end'):
        return Response(status=400)
    
    topic = request.args.get('topic')
    start = int(request.args.get('start'))
    end = int(request.args.get('end'))
    
    collection = mongo.db.topics
    res = collection.find_one(
        {'topic': topic},
        {'notifications': {'$slice': [-end, end - start]}, '_id': 0}
    )
    if res is None:
        return Response(status=204)

    res["notifications"].reverse()
    if res is None:
        return Response(status=204)
    return jsonify(res['notifications'])

"""
Publish message to a topic - Given the name of industry and notification send push
notifications to all the endpoint devices subscribed to that topic
"""
@app.route('/api/v1/topics/publish', methods=["POST"])
def publish_to_a_topic():
    if not request.json or not request.json.get('notification') or not request.json.get('topic'):
        return Response(status=400)

    topic_name = request.json.get('topic')
    notification = request.json.get('notification')

    collection = mongo.db.topics

    topic_document = collection.find_one({'topic': topic_name})
    if not topic_document:
        return Response(status=400)
    
    subscribers = topic_document['subscribers']
    publish.queue(subscribers, notification, topic_name)
    
    return Response(status=200)