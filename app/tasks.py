from pywebpush import webpush
from app import app, mongo, rq
import json

@rq.job('webpush-jobs')
def send_web_push(subscription_information, message_body, link):
    return webpush(
        subscription_info=subscription_information,
        data=json.dumps({'message': message_body, 'link': link}),
        vapid_private_key=app.config["VAPID_PRIVATE_KEY"],
        vapid_claims=app.config["VAPID_CLAIMS"]
    )

@rq.job('db-jobs')
def add_notification_to_db(industry, message, link):
    collection = mongo.db.industries
    collection.update_one({'industry': industry}, {'$push': {'notifications': {'message': message, 'link': link}}})
    