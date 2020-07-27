from flask import render_template, jsonify, Response, request
from app import app, mongo
from app.tasks import send_web_push, add_notification_to_db


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
        print("Not json")
        return Response(status=400)
    
    industry = request.json.get('industry')
    message = request.json.get('message')
    link = request.json.get('link')

    collection = mongo.db.industries
    industry_document = collection.find_one({'industry': industry})
    if not industry_document:
        print("No such industry")
        return Response(status=400)

    tokens = industry_document['subtoken']

    for token in tokens:
        send_web_push.queue(token, message, link)
    
    add_notification_to_db.queue(industry, message, link)
    
    return Response(status=200)
