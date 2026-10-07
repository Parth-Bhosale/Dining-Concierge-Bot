import json

def lambda_handler(event, context):
    response = {
        "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": "1",
                    "text": "I'm still under development. Please come back later.",
                    "timestamp": "2026-10-06T00:00:00Z"
                }
            }
        ]
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(response)
    }
