"""
Audit Engine - AWS Bedrock Knowledge Base Integration (Advanced Three-Tier Dynamic RAG)

Architecture:
1. TIER 1 (Triage & Query Decomposition): Amazon Nova Micro analyzes the incoming contract
   and dynamically generates targeted search queries for each legal obligation.
2. TIER 2 (Multi-Query Retrieval): Bedrock Agent Runtime queries OpenSearch Serverless
   with each dynamic query, deduplicating matching policy chunks.
3. TIER 3 (Synthesis & Audit): Amazon Nova Lite / Claude evaluates the contract
   clause-by-clause against the retrieved grounding chunks at Temperature 0.0.
"""

import os
import json
import re
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

load_dotenv()

# Model IDs
DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
MICRO_MODEL_ID = "amazon.nova-micro-v1:0"
CLAUDE_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

def get_clients(region_name="us-east-1"):
    """
    Initializes Bedrock Agent Runtime and Bedrock Runtime clients with adaptive retries.
    """
    retry_config = Config(
        retries={
            "max_attempts": 5,
            "mode": "adaptive"
        }
    )
    agent_client = boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=region_name,
        config=retry_config
    )
    runtime_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=region_name,
        config=retry_config
    )
    return agent_client, runtime_client

def generate_dynamic_queries(contract_text: str, runtime_client, model_id: str = MICRO_MODEL_ID) -> list:
    """
    Tier 1: Uses Amazon Nova Micro to inspect the contract and dynamically
    generate targeted retrieval queries covering all distinct legal risk areas.
    """
    prompt = f"""You are a Legal Procurement Assistant.
Analyze the following vendor contract and identify all distinct obligations, risk areas, and legal clauses.
Output exactly 4 to 6 short, focused search queries (one per line) to retrieve matching company policies from our Knowledge Base.

Do not number them. Do not include bullet points. Output only the plain queries, one per line.

VENDOR CONTRACT:
{contract_text}
"""
    try:
        response = runtime_client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.0, "maxTokens": 256}
        )
        raw_output = response["output"]["message"]["content"][0]["text"]
        lines = [line.strip().lstrip("-").lstrip("1234567890.").strip() for line in raw_output.split("\n") if line.strip()]
        return lines if lines else ["payment terms", "limitation of liability", "data residency", "governing law"]
    except Exception as e:
        print(f"Warning: Dynamic query generation fallback: {e}")
        # Fallback to standard baseline categories if triage model fails
        return [
            "payment terms and invoicing",
            "limitation of liability cap and data breach exceptions",
            "data residency, storage, and cross-border transfer",
            "incident and security breach notification SLA",
            "intellectual property and work product ownership",
            "governing law and jurisdiction"
        ]

def _parse_audit_json(raw_text: str):
    """Extracts and parses JSON from the LLM response (handles optional markdown fences)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw_text or "").strip(), flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _format_structured_markdown(data: dict) -> str:
    """Formats the structured audit JSON into a clean Markdown report."""
    verdict = str(data.get("overall_verdict", "NEEDS AMENDMENT")).replace("_", " ")
    lines = [
        "## Executive Summary",
        "",
        str(data.get("executive_summary") or "Compliance evaluation completed.").strip(),
        "",
        f"**Overall Verdict:** [{verdict}]",
        "",
    ]

    redlines = data.get("non_negotiable_redlines") or []
    if redlines:
        lines.append("### Priority Non-Negotiable Redlines")
        lines.extend(f"- {r}" for r in redlines if str(r).strip())
        lines.append("")

    lines.extend(["---", "", "## Clause-by-Clause Findings", ""])

    for idx, f in enumerate(data.get("findings", []), start=1):
        if not isinstance(f, dict):
            continue
        lines.append(f"### {idx}. {f.get('category', f'Clause {idx}')}")
        lines.append(f"- **Status:** [{f.get('status', 'COMPLIANT')}] · **Risk Severity:** [{f.get('risk_severity', 'NONE')}]")
        if f.get("vendor_clause"):
            lines.extend(["- **Vendor Clause:**", f"  > {f['vendor_clause']}"])
        if f.get("policy_requirement"):
            lines.append(f"- **Policy Requirement:** {f['policy_requirement']}")
        if f.get("analysis"):
            lines.append(f"- **Compliance Analysis:** {f['analysis']}")
        redline = f.get("recommended_redline")
        if redline and str(redline).strip().lower() not in ("null", "none", "n/a"):
            lines.extend(["- **Recommended Redline Language:**", f"  > {redline}"])
        lines.append("")

    return "\n".join(lines).strip()


def audit_contract_with_kb(contract_text: str, kb_id: str, model_id: str = DEFAULT_MODEL_ID, region: str = "us-east-1") -> dict:
    """
    Audits a contract using Advanced Three-Tier Dynamic RAG (Nova Micro + Knowledge Base + Nova Lite).
    """
    if not kb_id or kb_id.strip() == "YOUR_KNOWLEDGE_BASE_ID":
        return {
            "success": False,
            "report": "",
            "citations": [],
            "dynamic_queries": [],
            "error": "Knowledge Base ID is missing. Please configure BEDROCK_KB_ID in .env or settings."
        }

    try:
        agent_client, runtime_client = get_clients(region_name=region)

        # -------------------------------------------------------------
        # STEP 1: DYNAMIC QUERY GENERATION (TIER 1 - NOVA MICRO)
        # -------------------------------------------------------------
        dynamic_queries = generate_dynamic_queries(contract_text, runtime_client, model_id=MICRO_MODEL_ID)

        # -------------------------------------------------------------
        # STEP 2: MULTI-QUERY RETRIEVAL & DEDUPLICATION (BEDROCK KB)
        # -------------------------------------------------------------
        seen_chunks = set()
        parsed_citations = []
        policy_context_blocks = []

        for query in dynamic_queries:
            try:
                retrieval_response = agent_client.retrieve(
                    knowledgeBaseId=kb_id.strip(),
                    retrievalQuery={"text": query}
                )
                retrieved_results = retrieval_response.get("retrievalResults", [])

                for result in retrieved_results:
                    content_text = result.get("content", {}).get("text", "")
                    # Deduplicate based on text fingerprint to keep prompt clean
                    if content_text and content_text not in seen_chunks:
                        seen_chunks.add(content_text)
                        location = result.get("location", {})
                        s3_uri = location.get("s3Location", {}).get("uri", "S3 Policy Document")
                        score = result.get("score", 0.0)

                        policy_context_blocks.append(f"[Policy Reference - Triggered by '{query}']:\n{content_text}")
                        parsed_citations.append({
                            "text": content_text,
                            "source": s3_uri,
                            "score": score,
                            "matched_query": query
                        })
            except Exception as query_err:
                print(f"Error querying KB for '{query}': {query_err}")

        # If multi-query didn't catch anything, do a general sweep
        if not policy_context_blocks:
            sweep_response = agent_client.retrieve(
                knowledgeBaseId=kb_id.strip(),
                retrievalQuery={"text": "corporate compliance policy requirements for vendors"}
            )
            for result in sweep_response.get("retrievalResults", []):
                content_text = result.get("content", {}).get("text", "")
                if content_text:
                    policy_context_blocks.append(content_text)
                    parsed_citations.append({
                        "text": content_text,
                        "source": result.get("location", {}).get("s3Location", {}).get("uri", "S3 Policy Document"),
                        "score": result.get("score", 0.0),
                        "matched_query": "General Policy Sweep"
                    })

        combined_policy_context = "\n\n".join(policy_context_blocks)

        # -------------------------------------------------------------
        # STEP 3: DEEP SYNTHESIS & AUDIT (TIER 3 - NOVA LITE / CLAUDE)
        # -------------------------------------------------------------
        prompt = f"""You are a Principal Enterprise Legal & Procurement Compliance Auditor.
Strictly evaluate the VENDOR CONTRACT against the RETRIEVED COMPANY COMPLIANCE POLICIES.

--- RETRIEVED COMPANY COMPLIANCE POLICIES (GROUND TRUTH) ---
{combined_policy_context}
--- END COMPANY POLICIES ---

--- VENDOR CONTRACT TO AUDIT ---
{contract_text}
--- END VENDOR CONTRACT ---

Return ONLY a single valid JSON object (no markdown fences, no commentary before or after) matching this exact schema:
{{
  "overall_verdict": "APPROVED | NEEDS_AMENDMENT | REJECTED",
  "executive_summary": "2-4 sentence executive summary of overall contract posture and primary compliance gaps.",
  "non_negotiable_redlines": [
    "Concise action item for each required redline (empty array if APPROVED)"
  ],
  "findings": [
    {{
      "category": "Category name (e.g., Payment & Invoicing Terms, Limitation of Liability & Caps, Data Protection & Residency, Incident & Breach Notification SLA, Intellectual Property & Work Product, Governing Law & Jurisdiction, or any other obligation/missing policy)",
      "status": "COMPLIANT | NON_COMPLIANT | MISSING",
      "risk_severity": "HIGH | MEDIUM | LOW | NONE",
      "vendor_clause": "Exact verbatim quote of the relevant vendor contract clause, or state clearly if omitted.",
      "policy_requirement": "Concise summary of the applicable company policy rule from the retrieved context.",
      "analysis": "1-2 clear sentences explaining why the clause passes or fails compliance.",
      "recommended_redline": "Clean, ready-to-insert replacement contract clause if NON_COMPLIANT or MISSING; null if COMPLIANT."
    }}
  ]
}}

RULES:
- Cover every relevant obligation in the contract AND any mandatory standard missing from the contract (Payment Terms, Limitation of Liability, Data Protection/Residency, Incident Breach SLA, Intellectual Property, Governing Law).
- Write clean, plain prose inside JSON strings—do NOT use markdown formatting characters (** or ## or >) inside JSON string values.
- Ensure all quotes inside JSON strings are properly escaped.
"""

        messages = [
            {"role": "user", "content": [{"text": prompt}]}
        ]

        converse_response = runtime_client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                "temperature": 0.0,
                "maxTokens": 4096
            }
        )

        output_text = converse_response["output"]["message"]["content"][0]["text"]
        structured = _parse_audit_json(output_text)

        if isinstance(structured, dict) and structured.get("findings"):
            formatted_report = _format_structured_markdown(structured)
        else:
            structured = None
            formatted_report = output_text

        return {
            "success": True,
            "report": formatted_report,
            "structured": structured,
            "citations": parsed_citations,
            "dynamic_queries": dynamic_queries,
            "error": None
        }

    except NoCredentialsError:
        return {
            "success": False,
            "report": "",
            "citations": [],
            "dynamic_queries": [],
            "error": "AWS Credentials not found. Please check AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY in .env."
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return {
            "success": False,
            "report": "",
            "citations": [],
            "dynamic_queries": [],
            "error": f"AWS Bedrock Error [{error_code}]: {error_msg}"
        }
    except Exception as e:
        return {
            "success": False,
            "report": "",
            "citations": [],
            "dynamic_queries": [],
            "error": f"Unexpected error: {str(e)}"
        }