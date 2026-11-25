# 🛡️ Enterprise Contract Compliance Auditor

> **Autonomous legal & procurement compliance auditor powered by AWS Bedrock Knowledge Bases and an advanced 3-Tier Model Cascading RAG architecture.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Amazon%20Bedrock-232F3E?style=flat&logo=amazonaws&logoColor=FF9900)](https://aws.amazon.com/bedrock/)
[![OpenSearch](https://img.shields.io/badge/Vector%20DB-OpenSearch%20Serverless-005EB8?style=flat&logo=opensearch&logoColor=white)](https://aws.amazon.com/opensearch-service/features/serverless/)

---

## 📌 Executive Overview

Reviewing vendor contracts against internal procurement and compliance policies manually is time-consuming and error-prone.

The **Enterprise Contract Compliance Auditor** uses a **3-Tier Dynamic RAG pipeline** built on AWS Bedrock:
1. **Dynamic Query Decomposition:** Uses **Amazon Nova Micro** (`amazon.nova-micro-v1:0`) to analyze the full incoming contract and generate 4–6 targeted policy retrieval queries (with a built-in fallback list if generation fails).
2. **Multi-Query Knowledge Base Retrieval:** Queries an **Amazon Bedrock Knowledge Base** (`bedrock-agent-runtime`) for each query and deduplicates matching policy chunks in memory (falling back to a general sweep if nothing matches).
3. **Policy-Grounded Synthesis:** Evaluates the contract clause-by-clause using **Amazon Nova Lite** (`amazon.nova-lite-v1:0`), **Amazon Nova Micro**, or **Anthropic Claude Haiku 4.5** at `temperature: 0.0`, returning structured JSON (parsed into a Markdown report), severity ratings, recommended redlines, and source citations.

---

## 🏗️ Technical Architecture

```
                                  INCOMING VENDOR CONTRACT
                               (Pasted or loaded in Streamlit)
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  TIER 1 ── DYNAMIC QUERY DECOMPOSITION (Amazon Nova Micro)                              │
│  • Reads contract obligations and identifies distinct legal risk vectors                │
│  • Generates 4–6 targeted search queries (e.g., "limitation of liability data breach")  │
│  • Falls back to baseline enterprise risk taxonomy on model exception                  │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
                                  Dynamic Retrieval Queries
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  TIER 2 ── MULTI-QUERY RETRIEVAL & DEDUPLICATION (Bedrock Agent Runtime)               │
│  • Queries Bedrock Knowledge Base (OpenSearch Serverless) via retrieve()               │
│  • Deduplicates retrieved policy chunks in memory via text matching                    │
│  • Collects S3 document URIs, relevance scores, and triggering queries                 │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
                               Retrieved Policy Chunks
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  TIER 3 ── POLICY-GROUNDED AUDIT SYNTHESIS (Nova Lite / Nova Micro / Claude Haiku 4.5) │
│  • Invokes Bedrock Converse API with retrieved policy chunks (temperature: 0.0)        │
│  • Evaluates clause compliance: [COMPLIANT], [NON_COMPLIANT], or [MISSING]             │
│  • Assigns risk severity: [HIGH], [MEDIUM], [LOW], or [NONE]                           │
│  • Drafts replacement redline contract language and formats Markdown report            │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
                                             ▼
                               STREAMLIT AUDIT DASHBOARD
                   Executive Summary · Clause Breakdown · Citations
```

### 3-Tier Model Cascading Breakdown

| Tier | Component | Model / Engine | Purpose |
|---|---|---|---|
| **Tier 1: Triage** | Query Decomposition | Amazon Nova Micro (`amazon.nova-micro-v1:0`) | Reads the full `contract_text` at `temperature: 0.0` to generate 4–6 search queries. |
| **Tier 2: Retrieval** | Vector Search | Bedrock Knowledge Base (`bedrock-agent-runtime`) | Retrieves relevant policy chunks from S3/OpenSearch and deduplicates them. |
| **Tier 3: Synthesis** | Compliance Reasoner | Amazon Nova Lite (`amazon.nova-lite-v1:0`) / Nova Micro / Claude Haiku 4.5 | Evaluates the contract against retrieved policy chunks (`temperature: 0.0`, `maxTokens: 4096`) and outputs verdict, findings, and redlines. |

---

## ✨ Key Features

- **Policy-Grounded RAG (`temperature: 0.0`):** Injects retrieved Knowledge Base chunks into the synthesis prompt and uses greedy decoding (`temperature: 0.0`) to reduce variance, returning raw source citations for human verification. *(Note: `temperature: 0.0` does not guarantee zero hallucinations—legal review of the citations and findings is still required.)*
- **Dynamic Policy Extraction:** Generates search queries directly from the contract text rather than relying solely on a static keyword list, with a 6-topic fallback taxonomy if Tier 1 fails.
- **Actionable Redlines:** For non-compliant or missing clauses, outputs replacement contract language alongside the verdict (`APPROVED`, `NEEDS_AMENDMENT`, or `REJECTED`).
- **Traceable Citations:** Each retrieved policy chunk includes its S3 document URI, relevance score, and triggering query.
- **Runtime Model & Region Flexibility:** Switch between Amazon Nova Lite, Amazon Nova Micro, and Anthropic Claude Haiku 4.5 across `us-east-1`, `us-west-2`, `eu-central-1`, and `ap-southeast-1` from the Streamlit sidebar.

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.9+**
- An **AWS Account** with:
  - Bedrock model access granted for **Amazon Nova Micro** and **Amazon Nova Lite** (or Claude Haiku 4.5)
  - An active **Bedrock Knowledge Base** (backed by S3 and OpenSearch Serverless)
  - AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) with Bedrock permissions

---

### Step 1: Clone and Set Up Virtual Environment

```bash
git clone https://github.com/YOUR_USERNAME/enterprise-contract-compliance-auditor.git
cd "enterprise-contract-compliance-auditor"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate
```

---

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Populate `.env` with your AWS credentials and Bedrock Knowledge Base ID:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_KB_ID=your_knowledge_base_id
```

> 🔒 **Security Notice:** `.env` contains sensitive secrets and is excluded in `.gitignore`. Never commit AWS credentials to public source control.

---

### Step 4: Run the Application

```bash
python -m streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## ☁️ AWS Bedrock Knowledge Base Setup

Follow these steps to set up your knowledge base in AWS:

### 1. Ingest Corporate Policies into S3
Create an S3 bucket and upload your organization's policy documents:
```bash
aws s3 mb s3://<your-policy-bucket-name> --region us-east-1
aws s3 cp data/company_policy.txt s3://<your-policy-bucket-name>/
```
*(You can also upload additional PDF, DOCX, or TXT policy documents.)*

### 2. Create the Bedrock Knowledge Base
1. Open the [AWS Bedrock Console](https://console.aws.amazon.com/bedrock) → **Knowledge Bases** → **Create Knowledge Base**.
2. **Data Source:** Select your S3 bucket (`s3://<your-policy-bucket-name>`).
3. **Embeddings Model:** Select **Amazon Titan Text Embeddings v2**.
4. **Vector Store:** Select **Quick create a new vector store (OpenSearch Serverless)**.
5. Click **Sync** to ingest and vectorize your documents.
6. Copy the generated **Knowledge Base ID** (10-character string, e.g. `<YOUR_KB_ID>`) into your `.env`.

### 3. Minimum IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockKnowledgeBaseAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve",
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📊 Observed Performance & Known Limitations

Measured end-to-end runs using `amazon.nova-micro-v1:0` (Tier 1) + `amazon.nova-lite-v1:0` (Tier 3) in `us-east-1`:

- **Observed Latency:** **~11–18 seconds** end-to-end across 6 test contracts (`14.88s` on `sample_contract_compliant.txt`, `15.26s` on `sample_contract_non_compliant.txt`, and `11.07s–18.17s` on stress-test contracts).
- **Verbatim Quote Grounding:** **100%** verbatim `vendor_clause` substring match across all 33 non-missing findings in the 6 tested contracts.
- **Verdict Accuracy on Sample Contracts:** Correctly returned `APPROVED` on `sample_contract_compliant.txt` and `REJECTED` on `sample_contract_non_compliant.txt`.
- **Known Limitations:**
  - **Prompt Injection Sensitivity:** Untrusted contract text is currently passed inside the same `user` prompt as the audit instructions; an adversarial prompt-injection test embedded in a contract successfully forced an `APPROVED` verdict.
  - **Reasoning Edge Cases:** Nova Lite can occasionally miss nuanced exceptions (e.g., conflating a general liability cap with uncapped data-breach requirements) or flag over-literal matches (e.g., failing to infer that `"Virginia, United States"` satisfies US residency).
  - **S3 Policy Sync:** Audits run against whatever policy documents are synced in your Bedrock Knowledge Base S3 bucket—ensure `data/company_policy.txt` and your S3 bucket stay in sync.

---

## 📁 Repository Structure

```
enterprise-contract-compliance-auditor/
├── app.py                              # Streamlit interactive web dashboard
├── audit_engine.py                     # Core 3-tier RAG audit engine (Boto3 + Bedrock)
├── requirements.txt                    # Python dependencies
├── .env.example                        # Template for environment configuration
├── .gitignore                          # Excludes secrets, venv, and local artifacts
│
└── data/
    ├── company_policy.txt              # Sample corporate compliance guidelines
    ├── sample_contract_compliant.txt   # Compliant test agreement
    └── sample_contract_non_compliant.txt # Non-compliant test agreement
```

---

## 🔒 Security & AWS Data Handling

- **AWS Account Boundary:** Requests are sent via `boto3` over TLS to your configured AWS regional Bedrock endpoints (`bedrock-runtime` and `bedrock-agent-runtime`).
- **Model Training Policy:** Per AWS Bedrock service terms, Amazon Bedrock does not use customer prompts or outputs to train foundation models.
- **Credential Safety:** Supports `.env` variables locally and standard `boto3` IAM roles / AWS SSO credentials in production. Keep `.env` out of version control (excluded in `.gitignore`).