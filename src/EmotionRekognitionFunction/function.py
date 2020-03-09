import json
from decimal import Decimal
from operator import itemgetter
import boto3
import os

rekogn = boto3.client('rekognition')
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')


class RekognitionEmotionsResult:
    def __init__(self, disgusted, confused, surprised, happy, calm, fear, sad):
        self.disgusted = disgusted
        self.confused = confused
        self.surprised = surprised
        self.happy = happy
        self.calm = calm
        self.fear = fear
        self.sad = sad


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
    emotion_result = RekognitionEmotionsResult(
        get_confidence_for_emotion_type(emotions, "DISGUSTED"),
        get_confidence_for_emotion_type(emotions, "CONFUSED"),
        get_confidence_for_emotion_type(emotions, "SURPRISED"),
        get_confidence_for_emotion_type(emotions, "HAPPY"),
        get_confidence_for_emotion_type(emotions, "CALM"),
        get_confidence_for_emotion_type(emotions, "FEAR"),
        get_confidence_for_emotion_type(emotions, "SAD")
    )
    return emotion_result


def save_emotions(image_id, emotion_result):
    table = dynamodb.Table(os.environ["IMAGE_FEATURES_TABLE"])
    response = table.put_item(Item={
        'imageId': image_id,
        'DISGUSTED': convert_to_decimal(emotion_result.disgusted),
        'CONFUSED': convert_to_decimal(emotion_result.confused),
        'SURPRISED': convert_to_decimal(emotion_result.surprised),
        'HAPPY': convert_to_decimal(emotion_result.happy),
        'CALM': convert_to_decimal(emotion_result.calm),
        'FEAR': convert_to_decimal(emotion_result.fear),
        'SAD': convert_to_decimal(emotion_result.surprised)
    })
    print(response)


def convert_to_decimal(float_number):
    return Decimal(str(round(float_number, 4)))


def get_confidence_for_emotion_type(emotions, emotion_type):
    return list(map(itemgetter("Confidence"), filter(lambda d: d["Type"] == emotion_type, emotions)))[0]