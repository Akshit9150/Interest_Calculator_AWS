import json
import re
import uuid
import os
from datetime import datetime
from decimal import Decimal
import boto3
import urllib.request

# -----------------------
# AWS SETUP
# -----------------------
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("InterestChatHistory")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# -----------------------
# GEMINI NLP PARSING (urllib)
# -----------------------
def parse_with_gemini(user_text):
    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not found")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
    )

    prompt = f"""
Extract interest calculation details as JSON ONLY.

Text:
"{user_text}"

Return JSON with:
principal (number),
rate (number),
time (number),
type ("simple" or "compound")
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        f"{url}?key={GEMINI_API_KEY}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        result = response.read().decode("utf-8")

    parsed = json.loads(result)
    text = parsed["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)

# -----------------------
# RULE-BASED NLP (FALLBACK)
# -----------------------
def parse_amount(text):
    text = text.lower()

    lakh = re.search(r'(\d+(\.\d+)?)\s*lakh', text)
    if lakh:
        return float(lakh.group(1)) * 100000

    thousand = re.search(r'(\d+(\.\d+)?)\s*thousand', text)
    if thousand:
        return float(thousand.group(1)) * 1000

    number = re.search(r'(\d{4,})', text)
    if number:
        return float(number.group(1))

    raise ValueError("Principal amount not found")

def parse_rate(text):
    rate = re.search(r'(\d+(\.\d+)?)\s*(%|percent)', text.lower())
    if rate:
        return float(rate.group(1))
    raise ValueError("Interest rate not found")

def parse_time(text):
    time = re.search(r'(\d+(\.\d+)?)\s*(year|years|yr)', text.lower())
    if time:
        return float(time.group(1))
    raise ValueError("Time period not found")

def parse_type(text):
    if "simple" in text.lower():
        return "simple"
    return "compound"

def rule_based_parse(text):
    return {
        "principal": parse_amount(text),
        "rate": parse_rate(text),
        "time": parse_time(text),
        "type": parse_type(text)
    }

# -----------------------
# INTEREST CALCULATION
# -----------------------
def calculate_interest(p, r, t, interest_type):
    if interest_type == "simple":
        interest = (p * r * t) / 100
        amount = p + interest
    else:
        amount = p * ((1 + r / 100) ** t)
        interest = amount - p

    return round(interest, 2), round(amount, 2)

# -----------------------
# LAMBDA HANDLER
# -----------------------
def lambda_handler(event, context):
    try:
        # ---------- SAFE BODY HANDLING ----------
        body = event.get("body")

        # If body is missing (Lambda test, OPTIONS, etc.)
        if body is None:
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({
                    "message": "Lambda is alive. Send POST request with JSON body."
                })
            }

        # If body is a string (API Gateway normal case)
        if isinstance(body, str):
            body = json.loads(body)

        user_message = body.get("message")
        if not user_message:
            raise ValueError("Missing 'message' in request body")

        # ---------- NLP PARSING ----------
        try:
            parsed = parse_with_gemini(user_message)
            source = "gemini"
        except Exception:
            parsed = rule_based_parse(user_message)
            source = "rule-based"

        principal = float(parsed["principal"])
        rate = float(parsed["rate"])
        time = float(parsed["time"])
        interest_type = parsed["type"]

        interest, final_amount = calculate_interest(
            principal, rate, time, interest_type
        )

        # ---------- STORE IN DYNAMODB ----------
        table.put_item(
            Item={
                "id": str(uuid.uuid4()),
                "query": user_message,
                "principal": Decimal(str(principal)),
                "rate": Decimal(str(rate)),
                "time": Decimal(str(time)),
                "type": interest_type,
                "interest": Decimal(str(interest)),
                "final_amount": Decimal(str(final_amount)),
                "source": source,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # ---------- RESPONSE ----------
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({
                "parsed_input": {
                    "principal": principal,
                    "rate": rate,
                    "time": time,
                    "type": interest_type
                },
                "interest": interest,
                "final_amount": final_amount,
                "parsed_by": source
            })
        }

    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }
