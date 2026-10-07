# Dining Concierge Bot


## Architecture

S3 Frontend
→ API Gateway
→ LF0
→ Amazon Lex
→ LF1
→ SQS
→ LF2
→ OpenSearch + DynamoDB
→ SES

LF2 is triggered every minute using EventBridge Scheduler.

End-to-End Flow
1. User sends a message through the S3-hosted frontend.
2. API Gateway invokes LF0.
3. LF0 forwards the message to Amazon Lex.
4. Lex collects dining preferences.
5. LF1 sends the completed request to SQS.
6. EventBridge Scheduler invokes LF2.
7. LF2 queries OpenSearch for restaurants matching the requested cuisine.
8. LF2 retrieves restaurant details from DynamoDB.
9. LF2 sends restaurant recommendations through Amazon SES.

## AWS Services Used

- Amazon S3
- API Gateway
- AWS Lambda
- Amazon Lex V2
- Amazon SQS
- Amazon DynamoDB
- Amazon OpenSearch Service
- Amazon SES
- Amazon EventBridge Scheduler

## Lambda Functions

### LF0
Receives chatbot requests from API Gateway and forwards the user message to Amazon Lex.

### LF1
Acts as the Lex code hook, collects dining preferences, and pushes completed requests to SQS.

### LF2
Reads dining requests from SQS, queries OpenSearch by cuisine, retrieves restaurant information from DynamoDB, and sends restaurant recommendations using SES.

## DiningSuggestionsIntent Slots

- Location
- Cuisine
- DiningTime
- NumberOfPeople
- Email

## Restaurant Data

Restaurant data was collected using the Yelp API.

DynamoDB table:

`yelp-restaurants`

Stores:

- BusinessID
- Name
- Address
- Coordinates
- NumberOfReviews
- Rating
- ZipCode
- insertedAtTimestamp

OpenSearch index:

`restaurants`

Stores:

- RestaurantID
- Cuisine

## Repository Structure

```text
frontend/
lambda-functions/
other-scripts/