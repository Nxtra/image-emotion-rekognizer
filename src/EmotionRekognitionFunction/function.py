import json
from decimal import Decimal
from operator import itemgetter
import boto3
import os

rekogn = boto3.client('rekognition')
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    emotion_result = detect_emotions(object_key, bucket_name)
    save_emotions(object_key, emotion_result)


def detect_emotions(object_key, bucket):
    response = rekogn.detect_faces(Image={'S3Object': {'Bucket': bucket, 'Name': object_key}}, Attributes=['ALL'])

    # This is only for pictures that contain one face
    face_detail = response['FaceDetails'][0]
    emotions = face_detail.get('Emotions')
    # Uncomment below if you want to print the emotions
    # print(json.dumps(faceDetail.get("Emotions"), indent=4, sort_keys=True))
    return emotions


def save_emotions(image_id, emotions):
    table = dynamodb.Table(os.environ["IMAGE_FEATURES_TABLE"])
    table.put_item(Item={
        'imageId': image_id,
        'DISGUSTED': get_confidence_for_emotion_type(emotions, "DISGUSTED"),
        'CONFUSED': get_confidence_for_emotion_type(emotions, "CONFUSED"),
        'SURPRISED': get_confidence_for_emotion_type(emotions, "SURPRISED"),
        'HAPPY': get_confidence_for_emotion_type(emotions, "HAPPY"),
        'CALM': get_confidence_for_emotion_type(emotions, "CALM"),
        'FEAR': get_confidence_for_emotion_type(emotions, "FEAR"),
        'SAD': get_confidence_for_emotion_type(emotions, "SAD")
    })


def get_confidence_for_emotion_type(emotions, emotion_type):
    confidence = list(map(itemgetter("Confidence"), filter(lambda d: d["Type"] == emotion_type, emotions)))[0]
    return convert_to_decimal(confidence)


def convert_to_decimal(float_number):
    return Decimal(str(round(float_number, 4)))

