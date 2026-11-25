# 🛡️ Enterprise Contract Compliance Auditor

> **Autonomous legal & procurement compliance auditor powered by AWS Bedrock Knowledge Bases and an advanced 3-Tier Model Cascading RAG architecture.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Amazon%20Bedrock-232F3E?style=flat&logo=amazonaws&logoColor=FF9900)](https://aws.amazon.com/bedrock/)
[![OpenSearch](https://img.shields.io/badge/Vector%20DB-OpenSearch%20Serverless-005EB8?style=flat&logo=opensearch&logoColor=white)](https://aws.amazon.com/opensearch-service/features/serverless/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

## 📌 Executive Overview

Reviewing vendor contracts (Master Services Agreements, Cloud SaaS Agreements, Statements of Work) against internal procurement and regulatory policies is traditionally a manual, multi-day bottleneck. Static keyword searches miss semantic variations, while naive single-prompt LLMs hallucinate rules or miss nuanced risk carve-outs.

The **Enterprise Contract Compliance Auditor** automates this workflow with a **3-Tier Dynamic RAG system**:
1. **Dynamic Query Decomposition:** Uses **Amazon Nova Micro** to read incoming contracts and dynamically generate targeted policy retrieval queries, preventing retrieval blind spots.
2. **Hybrid Vector Retrieval:** Queries an **Amazon Bedrock Knowledge Base** backed by **OpenSearch Serverless**, deduplicating matching policy chunks in memory.
3. **Deterministic Synthesis:** Evaluates clauses using **Amazon Nova Lite** (or Claude Haiku 4.5) strictly against retrieved ground truth at `temperature: 0.0`, outputting structured verdicts, severity ratings, and replacement redline contract language.

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
│  • Bedrock Knowledge Base (OpenSearch Serverless Vector Index)                         │
│  • Amazon Titan Text Embeddings v2 (Dense + Sparse Hybrid Search)                      │
│  • Deduplicates retrieved policy chunks via text fingerprinting                        │
│  • Caches S3 document URIs, relevance scores, and query triggers                       │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
                               Retrieved Policy Chunks (Ground Truth)
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  TIER 3 ── DETERMINISTIC AUDIT SYNTHESIS (Amazon Nova Lite / Claude Haiku 4.5)         │
│  • Invokes Bedrock Converse API with prompt-anchored ground truth (temperature: 0.0)   │
│  • Evaluates clause compliance: [COMPLIANT], [NON-COMPLIANT], or [MISSING]             │
│  • Assigns risk severity: [HIGH], [MEDIUM], [LOW], or [NONE]                           │
│  • Drafts ready-to-insert replacement redline contract language                        │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
                                             ▼
                               STREAMLIT AUDIT DASHBOARD
                   Executive Summary · Clause Breakdown · Citations
```

### 3-Tier Model Cascading Breakdown

| Tier | Component | Model / Engine | Latency | Purpose |
|---|---|---|---|---|
| **Tier 1: Triage** | Query Decomposition | Amazon Nova Micro (`amazon.nova-micro-v1:0`) | ~200 ms | Dissects the contract to generate focused search strings matching all obligations. |
| **Tier 2: Retrieval** | Hybrid Vector Search | Bedrock Knowledge Base + OpenSearch Serverless | ~350 ms | Fetches semantically relevant policy chunks from S3 and deduplicates chunks. |
| **Tier 3: Synthesis** | Compliance Reasoner | Amazon Nova Lite (`amazon.nova-lite-v1:0`) | ~1.2 s | Clause-by-clause audit against ground truth; writes executive verdict & redlines. |

---

## ✨ Key Features

- **Zero-Hallucination Grounding:** The synthesis prompt strictly constrains the foundation model to retrieved Knowledge Base chunks at `temperature: 0.0`.
- **Dynamic Policy Extraction:** Eliminates the rigidity of hardcoded search terms; unexpected contract provisions (e.g., offshore data replication, IP carve-outs) are dynamically searched.
- **Actionable Redlines:** For every non-compliant or missing clause, the engine provides exact replacement legal language ready to paste into redline drafts.
- **Traceable Citations:** Every finding links to an exact S3 policy document chunk, relevance score (e.g., `0.892`), and the triggering query.
- **Runtime Model & Region Flexibility:** Seamlessly switch between Amazon Nova Lite, Amazon Nova Micro, and Anthropic Claude Haiku 4.5 across AWS regions directly from the UI.

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

## 💰 Cost & Latency Economics

By implementing **Model Cascading** (Nova Micro for query decomposition + Nova Lite for synthesis), this system delivers significant cost and performance advantages over single-tier frontier LLM setups:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ COST PER AUDIT: ~$0.0008                                                    │
│                                                                             │
│ • Tier 1 (Nova Micro, ~400 tokens):   $0.000014                             │
│ • Tier 2 (OpenSearch Retrieval):      Serverless Base OCU                   │
│ • Tier 3 (Nova Lite, ~2,200 tokens):  $0.000780                             │
│                                                                             │
│ TOTAL COST: Less than 1/10th of a cent per contract audit.                  │
│ LATENCY: Sub-2 seconds total execution time.                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

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
    ├── company_policy.txt              # Baseline golden corporate compliance guidelines
    ├── sample_contract_compliant.txt   # Fully compliant test agreement (passes audit)
    └── sample_contract_non_compliant.txt # High-risk test agreement (triggers redlines)
```

---

## 🔒 Enterprise Security & Compliance

- **VPC & Data Boundary:** All contract documents and policy chunks are processed entirely within your AWS tenant. No prompts or vendor data are sent to public third-party APIs.
- **Zero Training Guarantee:** Amazon Bedrock foundation models do not retain or use customer inputs or outputs for model training.
- **Credential Safety:** Supports standard AWS credential chains, IAM Identity Center (SSO), and temporary role assumption via `boto3`.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.