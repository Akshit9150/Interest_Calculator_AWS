# Interest_Calculator_AWS

# 💰 Interest Calculator – Serverless AWS Application

A **serverless Interest Calculator** built using **AWS cloud services** and **Generative AI (Gemini API)**.  
The application calculates interest, generates AI-powered explanations, and stores user history using a scalable, cloud-native architecture.

---

## 🚀 Features

- 📊 Interest calculation (Simple / Compound)
- 🤖 AI-generated explanation using **Gemini API**
- ☁️ Fully serverless architecture
- 🗂️ Persistent calculation history storage
- 📈 Logging & monitoring with CloudWatch
- 🔐 Secure IAM-based access

---

## 🏗️ Architecture

 - Client (Frontend / Postman)
 - |
 - v
 - API Gateway
 - |
 - v
 - AWS Lambda
 - |
 - ├── Gemini API (AI explanation)
 - ├── DynamoDB (history storage)
 - ├── S3 (optional static/log storage)
 - |
 - CloudWatch (logs & metrics)

---

## 🛠️ Tech Stack

### AWS Services
- **AWS Lambda** – Serverless backend logic
- **Amazon API Gateway** – REST API
- **Amazon DynamoDB** – Stores interest calculation history
- **Amazon S3** – Static data / logs (if enabled)
- **Amazon CloudWatch** – Monitoring and logs

### AI
- **Gemini API** – Generates explanations for calculated interest

---

## ⚙️ How It Works

1. User sends interest details via API request
2. API Gateway triggers Lambda
3. Lambda:
   - Calculates interest
   - Calls Gemini API for explanation
   - Stores result in DynamoDB
4. Response returned to the client
5. Logs recorded in CloudWatch

---

## 📦 Sample API Request

```json
{
  "principal": 10000,
  "rate": 5,
  "time": 2
}
```
-- response
```
{
  "interest": 1000,
  "explanation": "At 5% annual interest over 2 years, your investment grows steadily..."
}
```
🔐 Security
 - IAM roles follow least privilege
 - Lambda permissions:
 - DynamoDB read/write
 - CloudWatch logging
 - S3 access (if enabled)
 - CORS enabled in API Gateway

📈 Monitoring
 - Lambda logs available in CloudWatch
 - API metrics: latency, invocations, errors
 - Easy debugging and performance tracking
