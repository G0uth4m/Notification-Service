from pywebpush import webpush
from app import app, mongo, rq
import json

@rq.job('webpush-jobs')
def send_web_push(token, notification):
    return webpush(
        subscription_info=token,
        data=json.dumps(notification),
        vapid_private_key=app.config["VAPID_PRIVATE_KEY"],
        vapid_claims=app.config["VAPID_CLAIMS"]
    )


@rq.job('db-jobs')
def add_notification_to_db(topic, notification):
    collection = mongo.db.topics
    collection.update_one({'topic': topic}, {'$push': {'notifications': notification}})


@rq.job('mobilepush-jobs')
def send_mobile_push(endpoint, notification):
    # TODO: Send push notifications to mobile phones
    pass


@rq.job('publish-jobs')
def publish(tokens, notification, topic_name):
    for token in tokens:
        send_web_push.queue(token, notification)
    
    # TODO: Send push notifications to mobile phones
        
    add_notification_to_db.queue(topic_name, notification)
    