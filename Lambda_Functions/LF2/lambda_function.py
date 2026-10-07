import json
import os
import boto3
import base64
import urllib.request


# Environment variables
OPENSEARCH_HOST = os.environ["OPENSEARCH_HOST"]
OPENSEARCH_USERNAME = os.environ["OPENSEARCH_USERNAME"]
OPENSEARCH_PASSWORD = os.environ["OPENSEARCH_PASSWORD"]

QUEUE_URL = os.environ["QUEUE_URL"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]


# AWS clients
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

table = dynamodb.Table("yelp-restaurants")


def search_restaurants(cuisine):
    url = f"https://{OPENSEARCH_HOST}/restaurants/_search"

    query = {
        "size": 3,
        "query": {
            "term": {
                "Cuisine": cuisine
            }
        }
    }

    credentials = f"{OPENSEARCH_USERNAME}:{OPENSEARCH_PASSWORD}"
    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    request = urllib.request.Request(
        url,
        data=json.dumps(query).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}"
        },
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    restaurant_ids = []

    for hit in result["hits"]["hits"]:
        restaurant_ids.append(
            hit["_source"]["RestaurantID"]
        )

    return restaurant_ids


def get_restaurant_details(restaurant_id):
    response = table.get_item(
        Key={
            "BusinessID": restaurant_id
        }
    )

    return response.get("Item")


def send_email(
    recipient,
    cuisine,
    location,
    dining_time,
    number_of_people,
    restaurants
):
    lines = []

    lines.append(
        f"Hello! Here are my {cuisine} restaurant suggestions "
        f"for {number_of_people} people."
    )

    lines.append("")

    for index, restaurant in enumerate(restaurants, start=1):

        name = restaurant.get("Name", "Unknown")
        address = restaurant.get("Address", "Address unavailable")
        rating = restaurant.get("Rating", "N/A")
        reviews = restaurant.get("NumberOfReviews", "N/A")

        lines.append(
            f"{index}. {name}\n"
            f"   Address: {address}\n"
            f"   Rating: {rating}\n"
            f"   Reviews: {reviews}"
        )

        lines.append("")

    lines.append(
        f"Requested location: {location}"
    )

    lines.append(
        f"Dining time: {dining_time}"
    )

    body = "\n".join(lines)

    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={
            "ToAddresses": [
                recipient
            ]
        },
        Message={
            "Subject": {
                "Data": "Your Dining Concierge Restaurant Suggestions"
            },
            "Body": {
                "Text": {
                    "Data": body
                }
            }
        }
    )


def lambda_handler(event, context):

    print("LF2 started")

    # Read one message from SQS
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1
    )

    messages = response.get("Messages", [])

    if not messages:
        print("No messages in SQS")
        return {
            "statusCode": 200,
            "body": "No messages available"
        }

    message = messages[0]

    body = json.loads(message["Body"])

    print("SQS message:")
    print(json.dumps(body))

    location = body["Location"]
    cuisine = body["Cuisine"]
    dining_time = body["DiningTime"]
    number_of_people = body["NumberOfPeople"]
    email = body["Email"]

    # Search OpenSearch
    restaurant_ids = search_restaurants(cuisine)

    print("Restaurant IDs:")
    print(restaurant_ids)

    restaurants = []

    # Get full details from DynamoDB
    for restaurant_id in restaurant_ids:

        restaurant = get_restaurant_details(
            restaurant_id
        )

        if restaurant:
            restaurants.append(restaurant)

    if not restaurants:
        raise Exception(
            f"No restaurants found for cuisine: {cuisine}"
        )

    # Send SES email
    send_email(
        email,
        cuisine,
        location,
        dining_time,
        number_of_people,
        restaurants
    )

    print("Email sent successfully")

    # Delete message only after successful processing
    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=message["ReceiptHandle"]
    )

    print("SQS message deleted")

    return {
        "statusCode": 200,
        "body": "Restaurant recommendations sent successfully"
    }