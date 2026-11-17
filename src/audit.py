"""Process synthetic authentication audit events delivered by SQS."""
import json
import os

def classify(event):
    if event.get("outcome") not in {"success", "failure"}:
        raise ValueError("Invalid outcome")
    return "review" if event["outcome"] == "failure" else "normal"

def handler(event, context):
    import boto3

    s3 = boto3.client("s3")
    table = boto3.resource("dynamodb").Table(os.environ["TABLE"])
    failures = []
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            event_id = record["messageId"]
            result = {"event_id": event_id, "verdict": classify(body)}
            key = f"audit/{event_id}.json"
            s3.put_object(Bucket=os.environ["BUCKET"], Key=key,
                          Body=json.dumps(result), ContentType="application/json")
            table.put_item(Item={**result, "object_key": key})
        except Exception:
            print(f"Processing failed for {record['messageId']}")
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
