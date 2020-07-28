from flask import render_template, jsonify, Response, request
from app import app, mongo
from app.tasks import send_web_push, add_notification_to_db
import requests


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/v1/vapid_public_key')
def get_vapid_public_key():
    pub_key = app.config['VAPID_PUBLIC_KEY']
    if pub_key is None:
        return Response(status=500)

    return jsonify({'public_key': pub_key})


@app.route('/api/v1/subscribe', methods=["POST"])
def post_subscription_token():
    if not request.json or not request.json.get('sub_token') or not request.json.get('industry'):
        return Response(status=400)

    collection = mongo.db.industries
    industry = request.json.get('industry')
    sub_token = request.json.get('sub_token')
    if collection.find_one({'industry': industry}):
        collection.update_one({'industry': industry}, {'$addToSet': {'sub_token': sub_token}})
    else:
        collection.insert_one({'industry': industry, 'subtoken': [sub_token], 'notifications': []})

    return Response(status=201)


@app.route('/api/v1/push', methods=["POST"])
def push_notifications():
    if not request.json or not request.json.get('industry') or not request.json.get('message') or not request.json.get('link'):
        return Response(status=400)
    
    industry = request.json.get('industry')
    message = request.json.get('message')
    link = request.json.get('link')

    collection = mongo.db.industries
    industry_document = collection.find_one({'industry': industry})
    if not industry_document:
        return Response(status=400)

    tokens = industry_document['subtoken']

    for token in tokens:
        send_web_push.queue(token, message, link)
    
    add_notification_to_db.queue(industry, message, link)
    
    return Response(status=200)


@app.route('/api/v1/topics/', methods=["POST"])
def create_topic():
    if not request.json or not request.json.get('topic'):
        return Response(status=400)

    topic_name = request.json.get('topic')

    collection = mongo.db.topics
    if collection.find_one({'topic': topic_name}):
        return Response(status=400)
    
    collection.insert_one({'topic': topic_name, 'industries': []})
    return Response(status=201)


@app.route('/api/v1/topics/subscribe', methods=["PUT"])
def subscribe_industry_to_topic():
    if not request.json or not request.json.get('topic') or not request.json.get('industry'):
        return Response(status=400)
    
    topic_name = request.json.get('topic')
    industry = request.json.get('industry')

    topics_collection = mongo.db.topics
    indistry_collection = mongo.db.industries

    if not indistry_collection.find_one({'industry': industry}) or not topics_collection.find_one({'topic': topic_name}):
        return Response(status=400)

    topics_collection.update_one({'topic': topic_name}, {'$addToSet': {'industries': industry}})
    return Response(status=200)


@app.route('/api/v1/topics/publish', methods=["POST"])
def publish_message_to_a_topic():
    if not request.json or not request.json.get('message') or not request.json.get('topic') or not request.json.get('link'):
        return Response(status=400)

    topic_name = request.json.get('topic')
    message = request.json.get('message')
    link = request.json.get('link')

    collection = mongo.db.topics

    topic_document = collection.find_one({'topic': topic_name})
    if not topic_document:
        return Response(status=400)
    
    industries = topic_document['industries']
    for industry in industries:
        post_data = {'industry': industry, 'message': message, 'link': link}
        response = requests.post('http://127.0.0.1:5000/api/v1/push', json=post_data)
    
    return Response(status=200)
