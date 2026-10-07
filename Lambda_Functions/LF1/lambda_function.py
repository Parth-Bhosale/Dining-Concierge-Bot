import json
import boto3

sqs = boto3.client("sqs")
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/339262218058/Q1"
def close(intent_name, message):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": intent_name,
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ]
    }


def delegate(intent_name, slots):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Delegate"
            },
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": "InProgress"
            }
        }
    }


def lambda_handler(event, context):
    print(json.dumps(event))

    intent = event["sessionState"]["intent"]
    intent_name = intent["name"]
    slots = intent.get("slots", {})

    if intent_name == "GreetingIntent":
        return close(
            intent_name,
            "Hi! How can I help you today?"
        )

    if intent_name == "ThankYouIntent":
        return close(
            intent_name,
            "You're welcome! Have a great day."
        )

    if intent_name == "DiningSuggestionsIntent":
        invocation_source = event.get("invocationSource")

        if invocation_source == "DialogCodeHook":
            return delegate(intent_name, slots)

        if invocation_source == "FulfillmentCodeHook":
            location = slots["Location"]["value"]["interpretedValue"]
            cuisine = slots["Cuisine"]["value"]["interpretedValue"]
            dining_time = slots["DiningTime"]["value"]["interpretedValue"]
            number_of_people = slots["NumberOfPeople"]["value"]["interpretedValue"]
            email = slots["Email"]["value"]["interpretedValue"]

            message = {
                "Location": location,
                "Cuisine": cuisine,
                "DiningTime": dining_time,
                "NumberOfPeople": number_of_people,
                "Email": email
            }

            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(message)
            )

            print("Location:", location)
            print("Cuisine:", cuisine)
            print("Dining Time:", dining_time)
            print("Number of People:", number_of_people)
            print("Email:", email)


            return close(
                intent_name,
                f"You're all set. I will send {cuisine} restaurant suggestions "
                f"for {number_of_people} people to {email} shortly."
            )

    return close(
        intent_name,
        "Sorry, I couldn't process your request."
    )