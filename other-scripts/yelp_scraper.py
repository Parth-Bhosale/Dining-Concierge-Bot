import os
import time
from datetime import datetime, timezone
from opensearchpy import OpenSearch, RequestsHttpConnection

import boto3
import requests
from dotenv import load_dotenv
load_dotenv()

OPENSEARCH_HOST = "search-restaurants-jqc45so7y6fa35e767ytezs77u.us-east-1.es.amazonaws.com"

OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

opensearch = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": 443}],
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
print("Username:", OPENSEARCH_USERNAME)
print("Password loaded:", OPENSEARCH_PASSWORD is not None)
print("Password length:", len(OPENSEARCH_PASSWORD) if OPENSEARCH_PASSWORD else 0)

print(opensearch.info())

def save_to_opensearch(restaurant_id, cuisine):
    document = {
        "RestaurantID": restaurant_id,
        "Cuisine": cuisine
    }

    opensearch.index(
        index="restaurants",
        id=restaurant_id,
        body=document,
        refresh=False
    )


load_dotenv()

YELP_API_KEY = os.getenv("YELP_API_KEY")

if not YELP_API_KEY:
    raise ValueError("YELP_API_KEY not found in .env")

YELP_URL = "https://api.yelp.com/v3/businesses/search"

HEADERS = {
    "Authorization": f"Bearer {YELP_API_KEY}"
}

CUISINES = {
    "Italian": "italian",
    "Chinese": "chinese",
    "Indian": "indpak",
    "Mexican": "mexican",
    "Japanese": "japanese"
}

TARGET_PER_CUISINE = 250

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("yelp-restaurants")


def fetch_restaurants(cuisine_name, yelp_category):
    restaurants = {}

    locations = [
        "Manhattan, NY",
        "Upper East Side, Manhattan, NY",
        "Upper West Side, Manhattan, NY",
        "Midtown Manhattan, NY",
        "Downtown Manhattan, NY"
    ]

    for location in locations:
        offset = 0

        while len(restaurants) < TARGET_PER_CUISINE and offset < 200:
            params = {
                "location": location,
                "categories": yelp_category,
                "limit": 50,
                "offset": offset
            }

            response = requests.get(
                YELP_URL,
                headers=HEADERS,
                params=params,
                timeout=15
            )

            if response.status_code != 200:
                print(
                    f"Yelp error for {cuisine_name}: "
                    f"{response.status_code} {response.text}"
                )
                break

            data = response.json()
            businesses = data.get("businesses", [])

            if not businesses:
                break

            for business in businesses:
                restaurants[business["id"]] = business

                if len(restaurants) >= TARGET_PER_CUISINE:
                    break

            print(
                f"{cuisine_name}: collected "
                f"{len(restaurants)}/{TARGET_PER_CUISINE}"
            )

            offset += 50
            time.sleep(0.2)

        if len(restaurants) >= TARGET_PER_CUISINE:
            break

    return list(restaurants.values())


def save_to_dynamodb(restaurant):
    location = restaurant.get("location", {})
    coordinates = restaurant.get("coordinates", {})

    address = ", ".join(location.get("display_address", []))

    item = {
        "BusinessID": restaurant["id"],
        "Name": restaurant.get("name", ""),
        "Address": address,
        "Coordinates": {
            "latitude": str(coordinates.get("latitude", "")),
            "longitude": str(coordinates.get("longitude", ""))
        },
        "NumberOfReviews": restaurant.get("review_count", 0),
        "Rating": str(restaurant.get("rating", "")),
        "ZipCode": location.get("zip_code", ""),
        "insertedAtTimestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }

    table.put_item(Item=item)


# def main():
#     total_unique = set()

#     for cuisine_name, category in CUISINES.items():
#         print(f"\nCollecting {cuisine_name} restaurants...")

#         restaurants = fetch_restaurants(
#             cuisine_name,
#             category
#         )

#         saved = 0

#         for restaurant in restaurants:
#             business_id = restaurant["id"]

#             if business_id in total_unique:
#                 continue

#             save_to_dynamodb(restaurant)

#             total_unique.add(business_id)
#             saved += 1

#         print(
#             f"Saved {saved} unique "
#             f"{cuisine_name} restaurants to DynamoDB"
#         )

#     print(
#         f"\nTotal unique restaurants saved: "
#         f"{len(total_unique)}"
#     )

#     for restaurant in restaurants:
#     business_id = restaurant["id"]

#     if business_id in total_unique:
#         continue

#     save_to_dynamodb(restaurant)

#     save_to_opensearch(
#         business_id,
#         cuisine_name
#     )

#     total_unique.add(business_id)
#     saved += 1
def main():
    total_unique = set()

    for cuisine_name, category in CUISINES.items():
        print(f"\nCollecting {cuisine_name} restaurants...")

        restaurants = fetch_restaurants(
            cuisine_name,
            category
        )

        saved = 0

        for restaurant in restaurants:
            business_id = restaurant["id"]

            if business_id in total_unique:
                continue

            save_to_dynamodb(restaurant)

            save_to_opensearch(
                business_id,
                cuisine_name
            )

            total_unique.add(business_id)
            saved += 1

        print(
            f"Saved {saved} unique "
            f"{cuisine_name} restaurants to DynamoDB and OpenSearch"
        )

    print(
        f"\nTotal unique restaurants saved: "
        f"{len(total_unique)}"
    )

if __name__ == "__main__":
    main()