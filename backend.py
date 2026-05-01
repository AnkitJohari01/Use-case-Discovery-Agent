from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import requests
import json
import os
import time
import re
import random
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

# Import initial knowledge base
from seed_data import SEED_USE_CASES

# ─────────────────────────────────────────────
# In-memory cache: { keyword -> {data, timestamp} }
# ─────────────────────────────────────────────
cache = {}
for uc in SEED_USE_CASES:
    keyword = uc["keyword"].lower().strip()
    cache[keyword] = {"data": uc, "timestamp": time.time()}

# Domain → list of use cases (for /discover endpoint)
domain_cache = {}  # { domain -> { "use_cases": [...], "timestamp": float } }

# ─────────────────────────────────────────────
# Seed domain knowledge (fast, static fallback)
# ─────────────────────────────────────────────
DOMAIN_SEED = {
    "finance": [
        {
            "id": 1,
            "title": "Real-Time Fraud Detection",
            "description": "Flags suspicious transactions the moment they occur using ML anomaly scoring. Reduces false positives while catching fraud rings that traditional rules miss.",
            "tech_stack": "Python, Apache Kafka, Isolation Forest, XGBoost, Redis, AWS SageMaker, PostgreSQL",
            "business_process": [
                "Customer initiates a payment",
                "Transaction event is streamed via Kafka",
                "ML model scores the transaction in <50ms",
                "High-risk transactions trigger an alert / soft-block",
                "Analyst reviews flagged cases on a dashboard"
            ],
            "data_flow": "Payment Gateway → Kafka Stream → Feature Engineering (Redis) → ML Scoring Engine → Alert Dashboard / Block API",
            "domain": "Finance",
            "subdomain": "Risk & Compliance",
            "ml_technique": "Isolation Forest + XGBoost",
            "input_data": "Transaction amount, location, device fingerprint, historical patterns",
            "value": "Reduces fraud losses by up to 40% with <0.1% false-positive rate",
            "futuristic_view": "Federated learning across banks without sharing raw data; GNN-based collusion detection",
            "client_ready_details": "REST API integrated with payment gateway; SHAP explanations for every alert; Evidently AI drift monitoring"
        },
        {
            "id": 2,
            "title": "Alternative Credit Scoring",
            "description": "Scores creditworthiness for thin-file customers using non-traditional data sources. Expands the addressable market while keeping default rates within acceptable bounds.",
            "tech_stack": "Python, LightGBM, Apache Spark, Snowflake, SHAP, REST APIs, Docker",
            "business_process": [
                "Applicant submits loan request",
                "Alternative data (utility bills, mobile usage) is collected via APIs",
                "Feature engineering pipeline runs on Spark",
                "LightGBM model produces a risk score + explanation",
                "Loan origination system receives score and auto-decides"
            ],
            "data_flow": "Open Banking APIs / Telco Data → Spark Pipeline → Snowflake DWH → LightGBM Scorer → Loan Origination System",
            "domain": "Finance",
            "subdomain": "Lending",
            "ml_technique": "Gradient Boosting (LightGBM)",
            "input_data": "Utility payments, mobile recharge history, rental records, bank statement cash flows",
            "value": "Increases approval rates by 25% while maintaining target default rate",
            "futuristic_view": "Continuous behavioural credit score updated daily via open banking feeds",
            "client_ready_details": "Batch + real-time scoring API; SHAP-based adverse action notices for regulatory compliance"
        },
        {
            "id": 3,
            "title": "Customer Churn Prediction",
            "description": "Identifies retail-banking customers at risk of closing accounts or switching providers. Enables proactive retention campaigns before revenue walks out the door.",
            "tech_stack": "Python, XGBoost, Airflow, Tableau, SQL Server, Salesforce CRM API",
            "business_process": [
                "Weekly batch job pulls 12-month customer activity data",
                "Feature engineering (RFM, product tenure, complaints)",
                "XGBoost model scores each customer",
                "Top 5% highest-risk customers flagged in CRM",
                "Relationship manager triggers personalised retention offer"
            ],
            "data_flow": "Core Banking System → Airflow ETL → Feature Store (SQL Server) → XGBoost Scorer → Salesforce CRM → RM Dashboard",
            "domain": "Finance",
            "subdomain": "Customer Retention",
            "ml_technique": "XGBoost Classifier",
            "input_data": "Transaction frequency, product holdings, NPS scores, complaint history, tenure",
            "value": "Reduces annual churn by 15-20%, saving ~$500 per retained customer",
            "futuristic_view": "Real-time churn signal from mobile app events triggering instant personalised nudges",
            "client_ready_details": "Weekly Airflow DAG; Tableau dashboard with segment drill-down; CRM webhook integration"
        },
        {
            "id": 4,
            "title": "Automated Invoice Processing",
            "description": "Extracts structured data from PDF/image invoices and posts entries directly to the ERP. Eliminates manual keying and cuts processing time from days to minutes.",
            "tech_stack": "Python, Google Vision API / Tesseract, FastAPI, RabbitMQ, PostgreSQL, SAP REST API",
            "business_process": [
                "Vendor uploads invoice to supplier portal",
                "Document queued in RabbitMQ",
                "OCR + NLP extracts fields (vendor, amount, line items, PO number)",
                "Validation rules run against open POs in ERP",
                "Matched invoices auto-post; exceptions routed to AP team"
            ],
            "data_flow": "Vendor Upload → RabbitMQ Queue → OCR Processor → Validation Engine → SAP ERP → AP Dashboard",
            "domain": "Finance",
            "subdomain": "Accounts Payable",
            "ml_technique": "OCR + Named Entity Recognition (spaCy)",
            "input_data": "PDF/image invoices, PO master data, vendor master",
            "value": "80% reduction in manual entry; processing cost drops from $12 to $1.50 per invoice",
            "futuristic_view": "Self-learning extraction models that improve with every corrected exception",
            "client_ready_details": "Dockerised microservice; SAP/Oracle connector; SLA dashboard for AP managers"
        },
        {
            "id": 5,
            "title": "Portfolio Risk Scoring",
            "description": "Quantifies market, credit, and liquidity risk across investment portfolios in near real-time. Helps risk officers make faster, data-driven hedging decisions.",
            "tech_stack": "Python, Monte Carlo Simulation, Pandas, QuantLib, Grafana, TimescaleDB, REST APIs",
            "business_process": [
                "Market data feeds refresh every 15 minutes",
                "Portfolio positions loaded from trading system",
                "VaR, CVaR, and stress-test scenarios computed",
                "Risk breaches trigger automated alerts",
                "Risk committee reviews Grafana dashboard"
            ],
            "data_flow": "Market Data Vendors (Bloomberg/Reuters) → TimescaleDB → Risk Engine (Python/QuantLib) → Grafana Dashboard → Alert System",
            "domain": "Finance",
            "subdomain": "Investment Risk",
            "ml_technique": "Monte Carlo + Historical Simulation (VaR/CVaR)",
            "input_data": "Asset prices, position data, volatility surfaces, correlation matrices",
            "value": "Risk reporting time reduced from 4 hours to 15 minutes; regulatory capital optimisation",
            "futuristic_view": "Real-time intraday VaR with NLP-driven news sentiment as a leading risk indicator",
            "client_ready_details": "Scheduled + on-demand risk runs; PDF regulatory report generator; Bloomberg API integration"
        },
        {
            "id": 6,
            "title": "Anti-Money Laundering (AML) Transaction Monitoring",
            "description": "Detects suspicious money-laundering patterns across millions of daily transactions using graph analytics and ML. Replaces rigid rule engines that generate overwhelming false-positive loads.",
            "tech_stack": "Python, Neo4j (Graph DB), Graph Neural Networks, Apache Flink, Elasticsearch, Power BI",
            "business_process": [
                "All transactions ingested via Flink streaming",
                "Graph edges built between accounts, beneficiaries, and entities",
                "GNN model scores transaction clusters for typologies (layering, smurfing)",
                "Suspicious activity reports (SARs) auto-drafted for high-score cases",
                "Compliance officer reviews, enriches, and files SARs"
            ],
            "data_flow": "Core Banking → Flink Stream → Neo4j Graph DB → GNN Scoring → Elasticsearch Index → Compliance Dashboard",
            "domain": "Finance",
            "subdomain": "Compliance",
            "ml_technique": "Graph Neural Network + Unsupervised Clustering",
            "input_data": "Transaction records, account relationships, beneficial owner data, geographic metadata",
            "value": "False-positive rate cut by 60%; investigator productivity +3x",
            "futuristic_view": "Cross-institutional AML network using privacy-preserving federated graph learning",
            "client_ready_details": "FATF-compliant SAR templates; FinCEN/FCA-ready audit trail; Explainability report per alert"
        }
    ],
    "healthcare": [
        {
            "id": 1,
            "title": "Patient Readmission Risk Prediction",
            "description": "Predicts which patients are likely to be re-hospitalised within 30 days of discharge. Enables care teams to intervene early with targeted follow-up.",
            "tech_stack": "Python, Random Forest, Apache Spark, Epic EHR API, HL7 FHIR, Tableau",
            "business_process": [
                "Patient discharge event triggers scoring pipeline",
                "EHR data (labs, vitals, diagnosis codes) extracted via FHIR API",
                "Random Forest model scores readmission risk",
                "High-risk patients flagged in discharge planning workflow",
                "Care coordinator schedules follow-up call / home visit"
            ],
            "data_flow": "Epic EHR → FHIR API → Spark Feature Pipeline → Risk Model → Discharge Dashboard → Care Coordinator",
            "domain": "Healthcare",
            "subdomain": "Clinical Operations",
            "ml_technique": "Random Forest Classifier",
            "input_data": "ICD codes, lab results, length of stay, prior admissions, social determinants",
            "value": "30-day readmission rate reduced by 18%; avoids ~$15K penalty per readmission",
            "futuristic_view": "Continuous monitoring via wearables post-discharge feeding live risk updates",
            "client_ready_details": "Epic-certified integration; HIPAA-compliant data pipeline; explainability via SHAP for clinicians"
        },
        {
            "id": 2,
            "title": "Medical Imaging Anomaly Detection",
            "description": "Automatically screens X-rays and CT scans for anomalies such as nodules, fractures, and masses. Acts as a triage assistant to help radiologists prioritise high-urgency cases.",
            "tech_stack": "Python, PyTorch, MONAI, DICOM, PACS Integration, FastAPI, PostgreSQL",
            "business_process": [
                "Scan acquired and pushed to PACS",
                "DICOM image sent to AI inference service",
                "Model produces bounding-box + confidence score per finding",
                "High-confidence findings surfaced first in radiologist worklist",
                "Radiologist reviews, confirms or overrides, generates report"
            ],
            "data_flow": "Imaging Device → PACS → DICOM Preprocessor → PyTorch Inference API → Worklist Prioritisation → Radiology Report",
            "domain": "Healthcare",
            "subdomain": "Diagnostics",
            "ml_technique": "CNN (ResNet/EfficientNet) + Object Detection (YOLO)",
            "input_data": "DICOM images (X-ray, CT, MRI), patient metadata",
            "value": "Radiologist read time cut by 30%; critical findings turnaround <1 hour",
            "futuristic_view": "Multimodal AI combining imaging + genomics + EHR for personalised diagnosis",
            "client_ready_details": "FDA 510(k)-class deployment checklist; HL7 FHIR result push; radiologist feedback loop for continuous learning"
        },
        {
            "id": 3,
            "title": "Drug Interaction & Adverse Event Detection",
            "description": "Screens patient medication lists for dangerous drug-drug interactions before prescriptions are finalised. Prevents adverse events that cause ~125,000 deaths annually in the US.",
            "tech_stack": "Python, Knowledge Graph (Neo4j), NLP (BioBERT), DrugBank API, Epic/Cerner Integration",
            "business_process": [
                "Physician enters new prescription in EHR",
                "Current medication list retrieved",
                "Knowledge graph + BioBERT checks all interaction pairs",
                "Severity-ranked alerts surfaced inline in prescribing workflow",
                "Pharmacist reviews and confirms or adjusts"
            ],
            "data_flow": "EHR Prescription Event → Medication List API → Interaction Graph (Neo4j) → NLP Severity Ranker → Inline EHR Alert",
            "domain": "Healthcare",
            "subdomain": "Patient Safety",
            "ml_technique": "Knowledge Graph + BioBERT NLP",
            "input_data": "Drug codes (RxNorm), patient allergies, active medication list, clinical notes",
            "value": "Adverse drug events reduced by 35%; malpractice exposure reduced",
            "futuristic_view": "Pharmacogenomics integration — personalising drug selection based on patient DNA",
            "client_ready_details": "Epic-certified CDS Hooks integration; HIPAA-compliant; real-time response <200ms"
        }
    ]
}

def _make_arch_diagram(data_flow: str, ml: str) -> str:
    """Build a compact single-line ASCII diagram from data_flow + ML technique."""
    parts = [p.strip() for p in data_flow.replace("→", "→").split("→")]
    if len(parts) < 2:
        return f"[Source] → [ETL] → [{ml}] → [Dashboard / API]"
    return " → ".join(f"[{p}]" for p in parts)


def get_domain_use_cases(domain: str) -> list:
    """Return seeded use cases for a domain, always injecting architecture_diagram."""
    domain_lower = domain.lower().strip()
    for key in DOMAIN_SEED:
        if key in domain_lower or domain_lower in key:
            # Inject architecture_diagram if missing
            for uc in DOMAIN_SEED[key]:
                if "architecture_diagram" not in uc:
                    uc["architecture_diagram"] = _make_arch_diagram(uc["data_flow"], uc["ml_technique"])
            return DOMAIN_SEED[key]
    # Build from seed_data cache for partial matches
    matches = []
    idx = 1
    for uc in SEED_USE_CASES:
        if domain_lower in uc.get("domain", "").lower() or domain_lower in uc.get("subdomain", "").lower():
            data_flow = f"Source Data → ETL Pipeline → {uc.get('ml_technique','ML Model')} → Output / Dashboard"
            matches.append({
                "id": idx,
                "title": uc.get("use_case_name", ""),
                "description": uc.get("description", ""),
                "tech_stack": uc.get("ml_technique", ""),
                "business_process": [
                    "Data collection from relevant source systems",
                    "Feature engineering and preprocessing",
                    "Model training and validation",
                    "Deployment as scoring API or batch pipeline",
                    "Monitoring and periodic retraining"
                ],
                "data_flow": data_flow,
                "architecture_diagram": _make_arch_diagram(data_flow, uc.get("ml_technique", "ML Model")),
                "domain": uc.get("domain", ""),
                "subdomain": uc.get("subdomain", ""),
                "ml_technique": uc.get("ml_technique", ""),
                "input_data": uc.get("input_data", ""),
                "value": uc.get("value", ""),
                "futuristic_view": uc.get("futuristic_view", ""),
                "client_ready_details": uc.get("client_ready_details", "")
            })
            idx += 1
    if matches:
        return matches
    return []


# ─────────────────────────────────────────────
# Universal Dynamic Generator (Phase 3)
# Handles ANY domain keyword — never returns empty
# ─────────────────────────────────────────────
UNIVERSAL_TEMPLATES = [
    {
        "title_tpl": "{Domain} Demand Forecasting",
        "desc_tpl": "Predicts future demand patterns in {domain} to optimise resources and reduce waste. Replaces manual guesswork with data-driven forecasting.",
        "tech": "Python, Prophet / XGBoost, Apache Airflow, PostgreSQL, Grafana",
        "process": ["Collect historical operational data", "Engineer time-series features (seasonality, trends)", "Train forecasting model", "Deploy batch scoring pipeline", "Monitor forecast accuracy monthly"],
        "ml": "Prophet / XGBoost Regressor",
        "input": "Historical records, calendar events, external signals (weather, market data)",
        "value": "Reduces over/under-provisioning by 20-35%, saving operational costs",
        "flow_tpl": "Operational Systems → ETL (Airflow) → Feature Store → [Prophet / XGBoost] → Forecast Dashboard",
        "subdomain": "Operations",
        "futuristic": "Real-time adaptive forecasting using streaming data and reinforcement learning.",
        "client_ready": "Airflow DAG for daily runs; Grafana dashboard; REST API for downstream systems."
    },
    {
        "title_tpl": "{Domain} Anomaly Detection",
        "desc_tpl": "Automatically flags unusual patterns and outliers in {domain} data before they escalate into costly problems. Uses unsupervised ML to detect what rules miss.",
        "tech": "Python, Isolation Forest, Autoencoder (PyTorch), Kafka, Elasticsearch, Kibana",
        "process": ["Stream operational data via Kafka", "Apply Isolation Forest for fast anomaly scoring", "Deep-dive flagged items with Autoencoder", "Alert ops team via Slack / PagerDuty", "Log all anomalies for audit"],
        "ml": "Isolation Forest + Autoencoder",
        "input": "Sensor readings, transaction logs, event streams, time-series metrics",
        "value": "Catches 85%+ of critical anomalies within minutes, reducing incident response time",
        "flow_tpl": "Data Stream (Kafka) → Preprocessor → [Isolation Forest + Autoencoder] → Alert Engine → Ops Dashboard",
        "subdomain": "Risk & Quality",
        "futuristic": "Self-healing systems that not only detect but auto-remediate anomalies.",
        "client_ready": "Kafka consumer microservice; PagerDuty + Slack integration; Kibana dashboard."
    },
    {
        "title_tpl": "{Domain} Customer Segmentation",
        "desc_tpl": "Groups {domain} customers or users into meaningful clusters to enable personalised outreach and resource allocation. Reveals hidden patterns invisible to manual analysis.",
        "tech": "Python, K-Means / DBSCAN, scikit-learn, Snowflake, Tableau, Salesforce API",
        "process": ["Extract customer/user behaviour data", "Normalise and engineer RFM features", "Run K-Means clustering with elbow-method tuning", "Label and profile each segment", "Push segments to CRM for targeted campaigns"],
        "ml": "K-Means Clustering / DBSCAN",
        "input": "Interaction history, transaction records, demographic attributes, engagement metrics",
        "value": "Increases campaign conversion rates by 25-40% through precise targeting",
        "flow_tpl": "CRM / Source DB → Snowflake ETL → Feature Engineering → [K-Means] → Segment Labels → Tableau / CRM",
        "subdomain": "Customer Analytics",
        "futuristic": "Dynamic micro-segmentation updated in real time from live event streams.",
        "client_ready": "Weekly Airflow batch; Tableau dashboard; Salesforce push API."
    },
    {
        "title_tpl": "{Domain} Predictive Maintenance",
        "desc_tpl": "Anticipates equipment failures and process breakdowns in {domain} before they occur, shifting costly reactive repairs to scheduled, targeted interventions.",
        "tech": "Python, Gradient Boosting (XGBoost), Survival Analysis, InfluxDB, Grafana, MQTT",
        "process": ["Ingest sensor / telemetry data via MQTT", "Compute rolling health indicators (vibration, temp, throughput)", "XGBoost predicts time-to-failure per asset", "Maintenance tickets auto-created in CMMS", "Track prediction accuracy vs actual failures"],
        "ml": "XGBoost Classifier + Survival Analysis (Kaplan-Meier)",
        "input": "IoT sensor readings (temperature, vibration, pressure), historical failure logs, maintenance records",
        "value": "Reduces unplanned downtime by 30-45%, cutting emergency maintenance costs",
        "flow_tpl": "IoT Sensors (MQTT) → InfluxDB → Feature Pipeline → [XGBoost + Survival Model] → CMMS Alert → Grafana",
        "subdomain": "Asset Management",
        "futuristic": "Digital twins continuously updated with live telemetry for real-time simulation.",
        "client_ready": "Edge MQTT collector; InfluxDB time-series storage; CMMS API integration."
    },
    {
        "title_tpl": "{Domain} Process Automation & Classification",
        "desc_tpl": "Automates high-volume repetitive classification and routing tasks in {domain} using NLP and ML, replacing manual triage with sub-second AI decisions.",
        "tech": "Python, FastText / DistilBERT, FastAPI, RabbitMQ, PostgreSQL, Docker",
        "process": ["Capture incoming items (documents, requests, tickets)", "NLP model classifies type and priority", "Auto-route to correct team or system", "Confidence-below-threshold items flagged for human review", "Feedback loop retrains model quarterly"],
        "ml": "FastText / DistilBERT Text Classifier",
        "input": "Text documents, forms, emails, tickets, structured metadata",
        "value": "Automates 70-80% of manual classification tasks, reducing processing time from hours to seconds",
        "flow_tpl": "Input Channel → RabbitMQ Queue → [NLP Classifier] → Router → Target System / Human Queue",
        "subdomain": "Process Automation",
        "futuristic": "Multi-modal classification combining text, images, and structured data in a unified model.",
        "client_ready": "FastAPI microservice; Docker deployment; RabbitMQ integration; human-in-the-loop queue UI."
    },
    {
        "title_tpl": "{Domain} Performance Scoring & Ranking",
        "desc_tpl": "Scores and ranks entities (products, suppliers, employees, assets) in {domain} on composite performance dimensions, enabling objective, data-driven decisions.",
        "tech": "Python, scikit-learn, SHAP, Pandas, FastAPI, Power BI",
        "process": ["Collect multi-dimensional performance data", "Normalise and weight KPIs per business rules", "Compute composite ML score per entity", "Rank and tier entities (top / mid / at-risk)", "Publish scorecard to Power BI dashboard"],
        "ml": "Weighted Scoring + Logistic Regression / Random Forest",
        "input": "KPI metrics, historical performance records, external benchmarks",
        "value": "Replaces subjective manual rankings with objective, auditable ML-driven scores",
        "flow_tpl": "Source KPI Systems → ETL → Feature Engineering → [Scoring Model + SHAP] → Scorecard API → Power BI",
        "subdomain": "Performance Management",
        "futuristic": "Continuous real-time scoring fed by live operational APIs, replacing static quarterly reviews.",
        "client_ready": "FastAPI scorecard endpoint; SHAP explanation per score; Power BI report pack."
    },
    {
        "title_tpl": "{Domain} Churn & Retention Prediction",
        "desc_tpl": "Identifies {domain} customers, subscribers, or stakeholders at risk of disengaging before they leave, enabling proactive retention actions at the right moment.",
        "tech": "Python, XGBoost, SHAP, Airflow, Salesforce / HubSpot API, SQL Server",
        "process": ["Pull 90-day engagement and activity history", "Engineer churn signals (recency, frequency, complaints)", "XGBoost scores each entity weekly", "Top 10% at-risk flagged in CRM with action recommendations", "Track retention campaign outcomes"],
        "ml": "XGBoost Classifier",
        "input": "Engagement logs, purchase/interaction history, support tickets, NPS scores",
        "value": "Reduces churn by 15-25%, with ROI typically exceeding implementation cost within 3 months",
        "flow_tpl": "CRM / App DB → Airflow ETL → Feature Store → [XGBoost] → Churn Score → CRM Alert → Retention Action",
        "subdomain": "Retention",
        "futuristic": "Real-time churn signals from live app events, triggering instant personalised nudges.",
        "client_ready": "Weekly Airflow DAG; CRM webhook; SHAP-powered explanation for each at-risk entity."
    },
    {
        "title_tpl": "{Domain} Intelligent Reporting & Insights",
        "desc_tpl": "Transforms raw {domain} data into auto-generated executive summaries and anomaly-flagged reports, eliminating hours of manual analysis each week.",
        "tech": "Python, Pandas, NLP (spaCy / GPT API), Apache Superset, PostgreSQL, Airflow",
        "process": ["Aggregate data from operational systems nightly", "Run statistical analysis and anomaly detection", "NLP layer generates plain-English narrative summaries", "Anomalies and trend changes highlighted automatically", "Report emailed to stakeholders or published to dashboard"],
        "ml": "Statistical Anomaly Detection + NLP Narrative Generation",
        "input": "Operational KPIs, financial metrics, event logs, time-series data",
        "value": "Saves 5-10 analyst-hours per week; ensures no critical signal is missed in reporting",
        "flow_tpl": "Source Systems → Airflow ETL → PostgreSQL → [Statistical Engine + NLP] → Report Generator → Email / Superset",
        "subdomain": "Business Intelligence",
        "futuristic": "Conversational BI — stakeholders ask questions in plain English and receive instant data-backed answers.",
        "client_ready": "Airflow-scheduled nightly run; Superset dashboard; email distribution list integration."
    },
    {
        "title_tpl": "{Domain} Resource Optimization",
        "desc_tpl": "Dynamically allocates {domain} resources based on predicted demand and constraints, minimizing waste and maximizing utilization.",
        "tech": "Python, PuLP / OR-Tools, Fastify, Redis, Vue.js",
        "process": ["Aggregate real-time resource availability", "Forecast near-term demand using time-series models", "Run optimization solver to match supply and demand", "Dispatch assignments automatically", "Monitor utilization metrics and adjust thresholds"],
        "ml": "Linear Programming + Time-Series Forecasting",
        "input": "Resource schedules, live constraints, historical demand data",
        "value": "Improves overall resource utilization by 15-20% and reduces idle times",
        "flow_tpl": "Constraint DB → Forecaster → [Optimization Engine] → Dispatch API → Dashboard",
        "subdomain": "Operations",
        "futuristic": "Fully autonomous multi-agent systems negotiating resources in real-time.",
        "client_ready": "Optimization API with constraint management; Real-time dispatch interface."
    },
    {
        "title_tpl": "{Domain} Fraud & Risk Scoring",
        "desc_tpl": "Identifies suspicious activities or high-risk entities in {domain} using behavioral profiling and graph networks.",
        "tech": "Python, LightGBM, Neo4j, Apache Flink, Elasticsearch",
        "process": ["Ingest real-time transaction/event streams", "Build and update entity behavior profiles", "Compute graph-based features for connected entities", "Score events using tree-based ensemble", "Route high-risk items to manual review queue"],
        "ml": "LightGBM + Graph Neural Networks",
        "input": "Event streams, user profiles, historical risk labels",
        "value": "Reduces false positives by 30% while catching complex organized anomalies",
        "flow_tpl": "Event Stream → [Graph Feature Engine + LightGBM] → Risk Score → Case Management",
        "subdomain": "Risk Management",
        "futuristic": "Federated risk models learning across organizations without sharing raw data.",
        "client_ready": "Real-time streaming pipeline; Graph-based investigation UI; Automated risk alerts."
    },
    {
        "title_tpl": "{Domain} Supply Chain Visibility",
        "desc_tpl": "Provides end-to-end predictive tracking for {domain} logistics, forecasting delays and suggesting alternate routing.",
        "tech": "Python, XGBoost, Kafka, PostgreSQL, React",
        "process": ["Collect multi-modal tracking data", "Integrate external factors (weather, traffic, ports)", "Predict arrival times and delay probabilities", "Generate alternate route suggestions for delayed nodes", "Update ETA dashboard in real-time"],
        "ml": "XGBoost Regression + Routing Heuristics",
        "input": "GPS feeds, schedule data, weather APIs, traffic reports",
        "value": "Decreases supply chain disruptions by anticipating delays 48 hours in advance",
        "flow_tpl": "Tracking Sources → Kafka Stream → [Predictive ETA Model] → Route Optimizer → Operations Dashboard",
        "subdomain": "Logistics & Supply Chain",
        "futuristic": "Autonomous drone/vehicle rerouting based on real-time disruption data.",
        "client_ready": "Live ETA tracking map; Automated delay notifications; Supplier integration APIs."
    },
    {
        "title_tpl": "{Domain} Sentiment & Voice of Customer",
        "desc_tpl": "Analyzes unstructured {domain} feedback to extract sentiment, intent, and actionable product insights at scale.",
        "tech": "Python, HuggingFace (RoBERTa), FastAPI, MongoDB, Metabase",
        "process": ["Scrape and ingest reviews, surveys, and support transcripts", "Clean and normalize text data", "Extract sentiment and key topic clusters using NLP", "Aggregate insights over time periods", "Generate automated product/service recommendations"],
        "ml": "Transformer-based NLP (RoBERTa / BERT)",
        "input": "Customer support tickets, survey responses, social media, review sites",
        "value": "Automates feedback analysis, highlighting critical issues 10x faster than manual review",
        "flow_tpl": "Feedback Channels → NLP Pipeline → [Sentiment & Topic Model] → Insight DB → Metabase",
        "subdomain": "Customer Experience",
        "futuristic": "Real-time emotion detection from voice and video interactions during support calls.",
        "client_ready": "Daily batch NLP processing; Interactive topic exploration dashboard; CRM integration."
    }
]

def generate_dynamic_use_cases(domain: str) -> list:
    """
    Generate 5-8 use cases for ANY domain keyword.
    Never returns empty — uses universal templates adapted to the domain.
    """
    # Capitalise first word for display
    domain_title = " ".join(w.capitalize() for w in domain.strip().split())
    result = []
    
    # Phase 5: Randomize selection for diversity
    num_to_pick = random.randint(5, min(8, len(UNIVERSAL_TEMPLATES)))
    selected_templates = random.sample(UNIVERSAL_TEMPLATES, num_to_pick)
    
    for idx, tpl in enumerate(selected_templates, start=1):
        data_flow = tpl["flow_tpl"].replace("{domain}", domain_title).replace("{Domain}", domain_title)
        arch = _make_arch_diagram(data_flow, tpl["ml"])
        result.append({
            "id": idx,
            "title": tpl["title_tpl"].replace("{Domain}", domain_title).replace("{domain}", domain_title.lower()),
            "description": tpl["desc_tpl"].replace("{domain}", domain_title.lower()).replace("{Domain}", domain_title),
            "tech_stack": tpl["tech"],
            "business_process": tpl["process"],
            "data_flow": data_flow,
            "architecture_diagram": arch,
            "domain": domain_title,
            "subdomain": tpl["subdomain"],
            "ml_technique": tpl["ml"],
            "input_data": tpl["input"],
            "value": tpl["value"],
            "futuristic_view": tpl["futuristic"],
            "client_ready_details": tpl["client_ready"]
        })
    return result



# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class UseCaseCard(BaseModel):
    id: int
    title: str
    description: str
    tech_stack: str
    business_process: List[str]
    data_flow: str
    architecture_diagram: str  # ASCII diagram shown on Phase-1 card
    domain: str
    subdomain: str
    ml_technique: str
    input_data: str
    value: str
    futuristic_view: str
    client_ready_details: str

class DiscoverResponse(BaseModel):
    domain: str
    use_cases: List[UseCaseCard]
    source: str

class FinalizeRequest(BaseModel):
    domain: str
    use_case_id: int

class FinalizeResponse(BaseModel):
    use_case: UseCaseCard
    kpis: List[str]
    action_plan: List[str]
    confirmation_message: str
    copy_ready_text: str      # Phase 4: full plain-text case study
    claude_prompt: str        # Phase 4: regeneration prompt for Claude

class SearchResponse(BaseModel):
    data: dict
    source: str

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/discover", response_model=DiscoverResponse)
def discover_use_cases(domain: str):
    """Return 5-8 use case cards for a given domain."""
    domain_key = domain.lower().strip()

    # Check domain cache
    if domain_key in domain_cache:
        if time.time() - domain_cache[domain_key]["timestamp"] < 86400:
            return DiscoverResponse(
                domain=domain,
                use_cases=domain_cache[domain_key]["use_cases"],
                source="cache"
            )

    use_cases_raw = get_domain_use_cases(domain_key)

    # PHASE 3: Never return 404 — always generate for any domain
    if not use_cases_raw:
        use_cases_raw = generate_dynamic_use_cases(domain)

    use_cases = [UseCaseCard(**uc) for uc in use_cases_raw]

    # Store in domain cache
    domain_cache[domain_key] = {
        "use_cases": [uc.model_dump() for uc in use_cases],
        "timestamp": time.time()
    }

    return DiscoverResponse(domain=domain, use_cases=use_cases, source="knowledge_base")


@app.post("/finalize", response_model=FinalizeResponse)
def finalize_use_case(req: FinalizeRequest):
    """Lock in a specific use case and return KPIs + action plan."""
    domain_key = req.domain.lower().strip()

    if domain_key not in domain_cache:
        raise HTTPException(status_code=400, detail="Domain not discovered yet. Call /discover first.")

    use_cases = domain_cache[domain_key]["use_cases"]
    match = next((uc for uc in use_cases if uc["id"] == req.use_case_id), None)

    if not match:
        raise HTTPException(status_code=404, detail=f"Use case ID {req.use_case_id} not found in domain '{req.domain}'.")

    uc = UseCaseCard(**match)

    # Define KPIs and action plan first (used in copy_ready_text below)
    kpis = [
        f"Primary value: {uc.value}",
        "Model accuracy >= 90% on hold-out test set",
        "Production latency <= 500ms per inference",
        "System uptime >= 99.5% SLA",
        "Monthly model drift report with retraining trigger"
    ]

    action_plan = [
        f"Step 1 — Data Audit: Inventory available data sources for '{uc.title}' and assess quality/completeness.",
        f"Step 2 — Environment Setup: Provision cloud environment and install core stack ({uc.tech_stack.split(',')[0].strip()}, etc.).",
        f"Step 3 — Prototype: Build an end-to-end notebook proof-of-concept using {uc.ml_technique}.",
        "Step 4 — Productionise: Wrap model in a FastAPI microservice, add CI/CD pipeline, and integrate with downstream systems.",
        "Step 5 — Monitor & Iterate: Deploy Evidently AI (or similar) for drift detection; schedule quarterly retraining reviews."
    ]

    # ── Phase 4: Copy-ready full case study ──────────────────────────
    readiness = {
        "Client Ready":    {"score": 8, "note": "Production-grade pipeline, explainability, SLA targets defined."},
        "Manager Ready":   {"score": 9, "note": "Clear KPIs, ROI estimate, and phased action plan included."},
        "Director Ready":  {"score": 7, "note": "Strategic value and competitive differentiation articulated."},
        "Futuristic":      {"score": 6, "note": "Next-gen capabilities identified; requires R&D investment."},
    }
    readiness_text = "\n".join(
        f"  {k}: {v['score']}/10 -- {v['note']}" for k, v in readiness.items()
    )
    process_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(uc.business_process))
    action_text  = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(action_plan))
    kpi_text     = "\n".join(f"  - {k}" for k in kpis)

    copy_ready_text = f"""Title: {uc.title}

Domain: {uc.domain} > {uc.subdomain}
ML Technique: {uc.ml_technique}

── Problem Statement ─────────────────────────────────────────────
{uc.description}

── Objective / Goal ──────────────────────────────────────────────
Automate and optimise {uc.title.lower()} using {uc.ml_technique}, delivering
measurable business value within 90 days of go-live.

── Target Audience ───────────────────────────────────────────────
{uc.domain} Analysts, Operations Managers, Data Engineering Teams,
Executive Sponsors, Compliance Officers.

── Solution Overview ─────────────────────────────────────────────
{uc.value}

── Key Features ──────────────────────────────────────────────────
  1. Automated end-to-end data pipeline with quality checks
  2. {uc.ml_technique} core model with SHAP explainability
  3. Real-time + batch scoring API
  4. Operational dashboard with KPI monitoring
  5. Drift detection and automated retraining trigger
  6. Full audit trail for compliance and governance

── Tech Stack ────────────────────────────────────────────────────
{uc.tech_stack}

── Architecture / Flow ───────────────────────────────────────────
{uc.architecture_diagram}

── Input Data ────────────────────────────────────────────────────
{uc.input_data}

── Business Process ──────────────────────────────────────────────
{process_text}

── Impact / Benefits (Quantified) ───────────────────────────────
{uc.value}

── Action Plan ───────────────────────────────────────────────────
{action_text}

── Key Performance Indicators (KPIs) ────────────────────────────
{kpi_text}

── Future Scope ──────────────────────────────────────────────────
{uc.futuristic_view}

── Client-Ready Implementation Notes ────────────────────────────
{uc.client_ready_details}

── ROI Estimate ──────────────────────────────────────────────────
Implementation estimated at 3-6 months ROI payback. Based on: {uc.value}.
Recommended baseline measurement in Phase 1 for precise projection.

── Readiness Scores ──────────────────────────────────────────────
{readiness_text}
"""

    # ── Phase 4: Claude regeneration prompt ──────────────────────────
    claude_prompt = f"""You are a senior product strategist and AI consultant. Please generate a detailed, professional use case for \"{uc.title}".

Context: {uc.description}

Domain: {uc.domain} | Subdomain: {uc.subdomain} | Core ML Technique: {uc.ml_technique}

The use case must include the following sections, with thorough, realistic content:
1. Problem Statement
2. Objective / Goal
3. Target Audience
4. Solution Overview
5. Key Features (5-8 bullets)
6. Tech Stack
7. Architecture / Flow (with an ASCII diagram)
8. Impact / Benefits (quantified wherever possible)
9. Challenges & How They Were Solved
10. Results / Metrics (KPIs)
11. ROI Estimate (with assumptions listed)
12. Future Scope
13. Readiness Scores (Client Ready / Manager Ready / Director Ready / Futuristic) out of 10 with a brief explanation for each.

Existing tech stack for reference: {uc.tech_stack}
Existing value statement: {uc.value}

Make it thorough, realistic, and ready to be presented to executive stakeholders.
Write in a clear, business-friendly tone. Output in markdown format."""

    return FinalizeResponse(
        use_case=uc,
        kpis=kpis,
        action_plan=action_plan,
        confirmation_message=f"This use case has been finalized. Below you'll find the complete copy-ready text and a prompt you can use with Claude Sonnet to generate an improved version.",
        copy_ready_text=copy_ready_text,
        claude_prompt=claude_prompt
    )


class CaseStudyRequest(BaseModel):
    domain: str
    use_case_id: int

class CaseStudyResponse(BaseModel):
    use_case: UseCaseCard
    problem_statement: str
    objective: str
    target_audience: List[str]
    solution_overview: str
    key_features: List[dict]   # [{title, description}]
    tech_stack_expanded: str
    architecture_steps: List[str]
    architecture_diagram: str
    dataset_requirements: List[str]
    model_details: dict         # {algorithm, training, evaluation_metrics}
    integration_points: List[str]
    risks_and_mitigations: List[dict]  # [{risk, mitigation}]
    success_metrics: List[str]
    timeline_estimate: List[dict]      # [{phase, duration, deliverable}]
    roi_estimate: str

# Pre-built case study knowledge per use case title
CASE_STUDY_DATA = {
    "Real-Time Fraud Detection": {
        "problem_statement": "Financial institutions lose billions annually to payment fraud. Traditional rule-based systems generate excessive false positives (blocking legitimate customers) while missing novel attack patterns. The latency of batch-based detection means fraud is often identified only after money has moved, making recovery difficult.",
        "objective": "Detect fraudulent transactions within 50ms of initiation with ≥95% recall and <0.5% false-positive rate, enabling real-time blocking before fund settlement.",
        "target_audience": ["Fraud Operations Analysts", "Risk & Compliance Officers", "Core Banking Engineers", "Payment Gateway Teams"],
        "solution_overview": "A streaming ML pipeline ingests every transaction via Apache Kafka, enriches it with customer behavioral features cached in Redis, and scores it using a two-stage model (Isolation Forest for anomaly pre-filtering + XGBoost for classification). Scores above threshold trigger an immediate soft-block via the Payment Gateway API and queue the case for analyst review in a dashboard. The system learns continuously from analyst feedback, reducing model drift.",
        "key_features": [
            {"title": "Sub-50ms Scoring", "description": "Feature lookup from Redis + XGBoost inference completes in under 50ms, enabling real-time blocking before payment settlement."},
            {"title": "Two-Stage Detection", "description": "Isolation Forest filters obvious anomalies; XGBoost refines with behavioral context — reducing false positives vs single-model approaches."},
            {"title": "Analyst Review Queue", "description": "Flagged transactions surface in a prioritised dashboard with SHAP explanations, so analysts understand WHY each case was flagged."},
            {"title": "Feedback Loop", "description": "Analyst verdicts (true fraud / false positive) are logged and used to retrain the model weekly."},
            {"title": "Drift Monitoring", "description": "Evidently AI tracks prediction distribution and feature drift, triggering alerts when model performance degrades."},
            {"title": "Case Management", "description": "Full audit trail per transaction: score, features used, model version, analyst action — for regulatory reporting."},
            {"title": "Multi-Channel Support", "description": "Handles card-present, card-not-present, ACH, wire, and mobile payment channels through a unified event schema."}
        ],
        "tech_stack_expanded": "Python 3.11, Apache Kafka, Apache Spark Streaming, XGBoost, Isolation Forest (scikit-learn), Redis 7, AWS SageMaker, PostgreSQL 15, FastAPI, Docker, Kubernetes, Evidently AI, Grafana, SHAP, Airflow",
        "architecture_steps": [
            "Payment Gateway emits a transaction event to Kafka topic `transactions.raw`",
            "Spark Streaming consumer reads the event, joins with customer profile from PostgreSQL",
            "Behavioral features (30-day spend average, location delta, device fingerprint) fetched from Redis feature store",
            "Isolation Forest scores the enriched vector — scores above 0.6 continue to Stage 2",
            "XGBoost classifier produces final fraud probability and SHAP explanation vector",
            "Score > threshold → POST to Payment Gateway `/block` API + insert to PostgreSQL `fraud_queue`",
            "Grafana dashboard renders real-time fraud rate, block rate, and model performance metrics",
            "Nightly Airflow DAG retrains model on analyst-labelled feedback from past 7 days"
        ],
        "architecture_diagram": """
Payment Gateway
      │
      ▼
 Kafka Topic
(transactions.raw)
      │
      ▼
Spark Streaming ──► Redis Feature Store
      │              (behavioral context)
      ▼
Isolation Forest
  (pre-filter)
      │ score > 0.6
      ▼
  XGBoost Classifier
  + SHAP Explainer
      │
  ┌───┴───────────────┐
  │ score > threshold  │ score < threshold
  ▼                    ▼
Block API          Allow Payment
+ Fraud Queue      (logged only)
  │
  ▼
Analyst Dashboard
(Grafana + PostgreSQL)
  │
  ▼
Feedback → Airflow Retraining DAG
""",
        "dataset_requirements": [
            "Minimum 12 months of historical transaction data (ideally 24 months)",
            "Labelled fraud cases — at least 10,000 confirmed fraud events for initial training",
            "Customer profile data: account age, product holdings, average spend, geography",
            "Device fingerprint and IP metadata per transaction",
            "Merchant category codes (MCC) and merchant risk ratings"
        ],
        "model_details": {
            "algorithm": "Stage 1: Isolation Forest (unsupervised anomaly). Stage 2: XGBoost Gradient Boosting Classifier",
            "training": "Weekly retraining on rolling 90-day window. SMOTE oversampling for class imbalance. 80/10/10 train/val/test split stratified by fraud label.",
            "evaluation_metrics": "AUC-ROC ≥ 0.97 | Precision ≥ 0.85 | Recall ≥ 0.95 | F1 ≥ 0.90 | False Positive Rate < 0.5%"
        },
        "integration_points": [
            "Payment Gateway — real-time block/allow decisions via REST API webhook",
            "Core Banking System — customer profile enrichment via nightly ETL",
            "Case Management / CRM — fraud queue cases pushed via API",
            "Regulatory Reporting System — SAR-ready export for FinCEN / FCA",
            "SIEM (Splunk) — alert events streamed for security correlation"
        ],
        "risks_and_mitigations": [
            {"risk": "High false-positive rate blocking legitimate customers", "mitigation": "Two-stage model architecture + analyst feedback loop to continuously reduce FP rate. Soft-block (customer verification) rather than hard-block for borderline scores."},
            {"risk": "Model drift as fraud patterns evolve", "mitigation": "Evidently AI monitoring with automated retraining trigger when PSI > 0.2 on key features."},
            {"risk": "Latency spike under peak transaction load", "mitigation": "Redis feature store pre-computes behavioral aggregates; Kubernetes HPA scales inference pods automatically."},
            {"risk": "Regulatory non-compliance on adverse action", "mitigation": "SHAP explanations stored per decision; audit log retained for 7 years per BSA requirements."}
        ],
        "success_metrics": [
            "Fraud loss reduction ≥ 40% vs. rule-based baseline within 6 months",
            "False positive rate < 0.5% (vs. industry average of 2-3%)",
            "Transaction scoring latency p99 < 50ms",
            "Analyst review queue cleared within 4 business hours SLA",
            "Model AUC-ROC ≥ 0.97 on monthly hold-out test set"
        ],
        "timeline_estimate": [
            {"phase": "Phase 1 — Data & Infrastructure", "duration": "3 weeks", "deliverable": "Kafka cluster, feature store, data pipeline, labelled dataset ready"},
            {"phase": "Phase 2 — Model Development", "duration": "4 weeks", "deliverable": "Trained XGBoost + Isolation Forest models, SHAP integration, evaluation report"},
            {"phase": "Phase 3 — API & Dashboard", "duration": "3 weeks", "deliverable": "FastAPI scoring endpoint, Grafana dashboard, analyst queue UI"},
            {"phase": "Phase 4 — Integration & UAT", "duration": "3 weeks", "deliverable": "Payment gateway integration, shadow mode testing, UAT sign-off"},
            {"phase": "Phase 5 — Production & Monitoring", "duration": "2 weeks", "deliverable": "Go-live, Evidently AI monitoring, retraining pipeline active"}
        ],
        "roi_estimate": "Based on industry benchmarks: $2M annual fraud loss → 40% reduction = $800K saved. Implementation cost ~$180K. ROI breakeven at month 3. 5-year NPV estimated at $3.2M."
    },
    "Alternative Credit Scoring": {
        "problem_statement": "1.7 billion adults globally are 'credit invisible' — they lack traditional credit history but are often creditworthy. Banks reject them using FICO-only models, missing significant market opportunity while these customers turn to predatory lenders.",
        "objective": "Score creditworthiness of thin-file applicants using alternative data, achieving default rates within ±2% of traditional portfolio while approving 25% more applicants.",
        "target_audience": ["Loan Underwriters", "Credit Risk Managers", "Product Managers (Lending)", "Compliance & Fair Lending Officers"],
        "solution_overview": "Alternative data sources (utility payments, mobile top-up patterns, rental records, open banking cash flows) are collected via APIs and enriched into a feature set. A LightGBM model trained on historical outcomes scores applicants in real time. SHAP values generate human-readable adverse action notices for declined applicants, satisfying fair lending regulations. The pipeline runs both batch (for pre-approved offers) and real-time (for point-of-application scoring).",
        "key_features": [
            {"title": "Alternative Data Ingestion", "description": "Pulls utility, telco, rental, and open banking data via certified APIs with applicant consent."},
            {"title": "Real-Time Scoring API", "description": "Sub-200ms scoring at loan application point, integrated directly into loan origination system."},
            {"title": "SHAP Adverse Action Notices", "description": "Automatically generates regulator-compliant decline reasons from SHAP feature importance."},
            {"title": "Fairness Monitoring", "description": "Monitors for disparate impact across protected classes (race, gender, age proxies) using AIF360."},
            {"title": "Batch Pre-Approval Pipeline", "description": "Weekly Spark batch job scores entire customer base for pre-approved offer targeting."},
            {"title": "Model Card & Governance", "description": "Full model documentation, version control, and approval workflow for credit model governance."},
            {"title": "Champion/Challenger Framework", "description": "Routes 10% of traffic to challenger models to test improvements without full deployment risk."}
        ],
        "tech_stack_expanded": "Python 3.11, LightGBM, Apache Spark, Snowflake, SHAP, IBM AIF360, FastAPI, Airflow, Docker, AWS S3, dbt, Great Expectations, MLflow, PostgreSQL",
        "architecture_steps": [
            "Applicant submits loan application — triggers real-time scoring request",
            "Consent management system confirms data sharing permissions",
            "Open Banking / Telco / Utility APIs called — data fetched and cached in S3",
            "Spark feature engineering pipeline transforms raw data into 120+ features",
            "LightGBM model scores applicant; SHAP values computed for top 5 features",
            "Score + SHAP explanation returned to Loan Origination System in <200ms",
            "Decision logged to Snowflake for audit; adverse action notice auto-generated if declined",
            "Weekly Airflow DAG retrains model on new outcome data (repayments, defaults)"
        ],
        "architecture_diagram": """
Loan Application Event
        │
        ▼
Consent Management API
        │
        ▼
Alternative Data APIs ──► S3 Raw Data Lake
(Open Banking, Telco,
 Utility, Rental)
        │
        ▼
Spark Feature Pipeline
(120+ engineered features)
        │
        ▼
LightGBM Scorer + SHAP
        │
   ┌────┴────────────┐
   ▼                  ▼
Approve            Decline
   │                  │
   └──────┬───────────┘
          ▼
  Loan Origination System
  + Snowflake Audit Log
  + Adverse Action Notice
          │
          ▼
  Airflow Retraining DAG
  (weekly, MLflow tracking)
""",
        "dataset_requirements": [
            "24 months of loan performance data (repayment / default outcomes)",
            "Alternative data for at least 50,000 historical applicants",
            "Demographic data for fairness testing (must be siloed from model features)",
            "Open Banking transaction feeds — minimum 6 months per applicant",
            "Credit bureau data for model calibration benchmarking"
        ],
        "model_details": {
            "algorithm": "LightGBM Gradient Boosted Trees — chosen for speed, handling of missing data, and interpretability via SHAP.",
            "training": "Rolling 12-month training window. Stratified k-fold cross-validation. Optuna hyperparameter tuning. Class imbalance handled via scale_pos_weight.",
            "evaluation_metrics": "AUC-ROC ≥ 0.78 | KS Statistic ≥ 40 | Gini ≥ 0.56 | Default rate within ±2% of target | Disparate Impact Ratio ≥ 0.8 (fair lending)"
        },
        "integration_points": [
            "Loan Origination System (LOS) — real-time score delivery via REST API",
            "Open Banking aggregator (Plaid / TrueLayer) — transaction data",
            "Credit Bureau — FICO pull for hybrid scoring",
            "CRM — pre-approved offer targeting list",
            "Regulatory reporting — model card + adverse action audit export"
        ],
        "risks_and_mitigations": [
            {"risk": "Disparate impact on protected classes", "mitigation": "AIF360 fairness monitoring in production; monthly disparate impact analysis; legal review before deployment."},
            {"risk": "Data availability gaps for some applicants", "mitigation": "Model handles missing features via LightGBM native NA handling; minimum data sufficiency check before scoring."},
            {"risk": "Regulatory model approval delays", "mitigation": "Model governance workflow with SR 11-7 compliant documentation built in from day one."}
        ],
        "success_metrics": [
            "Approval rate increase ≥ 25% for thin-file segment",
            "Default rate within ±2% of traditional portfolio",
            "Disparate Impact Ratio ≥ 0.80 across all protected classes",
            "Adverse action notice generation < 1 second",
            "Model AUC-ROC ≥ 0.78 on monthly hold-out"
        ],
        "timeline_estimate": [
            {"phase": "Phase 1 — Data Sourcing & Consent Framework", "duration": "4 weeks", "deliverable": "API integrations, consent UI, data pipeline to S3"},
            {"phase": "Phase 2 — Feature Engineering & Model Training", "duration": "5 weeks", "deliverable": "120+ features, trained LightGBM, fairness validation report"},
            {"phase": "Phase 3 — API & LOS Integration", "duration": "3 weeks", "deliverable": "Scoring API, LOS integration, adverse action notice generator"},
            {"phase": "Phase 4 — Regulatory Review & UAT", "duration": "4 weeks", "deliverable": "SR 11-7 model documentation, legal sign-off, UAT"},
            {"phase": "Phase 5 — Pilot & Scale", "duration": "3 weeks", "deliverable": "Pilot with 1,000 applicants, performance review, full rollout"}
        ],
        "roi_estimate": "Addressable market expansion: 25% more approvals on 10,000 monthly applicants = 2,500 new loans. At $5K average loan margin = $12.5M incremental annual revenue. Implementation cost ~$220K. ROI breakeven at month 3."
    }
}

def generate_generic_case_study(uc: dict) -> dict:
    """Generate a structured case study for any use case not in CASE_STUDY_DATA."""
    title = uc["title"]
    domain = uc["domain"]
    subdomain = uc["subdomain"]
    ml = uc["ml_technique"]
    tech = uc["tech_stack"]
    desc = uc["description"]
    value = uc["value"]
    steps = uc["business_process"]
    data_flow = uc["data_flow"]

    return {
        "problem_statement": f"Organisations in {domain} / {subdomain} face significant operational challenges that {title} addresses. {desc} Without an intelligent, data-driven approach, teams rely on manual processes that are slow, error-prone, and unable to scale.",
        "objective": f"Automate and optimise {title.lower()} using {ml}, delivering measurable improvements within 90 days of go-live. {value}",
        "target_audience": [f"{domain} Analysts", f"{subdomain} Managers", "Data Engineering Teams", "Business Intelligence / Reporting Teams", "Executive Sponsors"],
        "solution_overview": f"The solution ingests data from relevant {domain} source systems, applies {ml} to generate predictions or decisions, and surfaces results through dashboards and automated workflows. The pipeline is fully automated, monitored for drift, and integrates with existing enterprise systems. {value}",
        "key_features": [
            {"title": "Automated Data Pipeline", "description": f"End-to-end ingestion from {domain} source systems with data quality checks and alerting."},
            {"title": f"{ml} Model", "description": f"Core intelligence layer using {ml} for accurate, explainable predictions."},
            {"title": "Real-Time / Batch Scoring", "description": "Flexible deployment supporting both on-demand API scoring and scheduled batch runs."},
            {"title": "Explainability Layer", "description": "SHAP-based explanations for every prediction, enabling business users to trust and act on outputs."},
            {"title": "Drift Monitoring", "description": "Automated monitoring of model and data drift with retraining triggers."},
            {"title": "Dashboard & Alerts", "description": "Operational dashboard surfacing KPIs, model performance, and actionable alerts."},
            {"title": "Audit & Governance", "description": "Full lineage tracking from data source to decision for compliance and reproducibility."}
        ],
        "tech_stack_expanded": f"{tech}, FastAPI, Docker, Kubernetes, Airflow, SHAP, Evidently AI, Grafana, MLflow, PostgreSQL",
        "architecture_steps": steps + [
            "Model outputs stored with full audit trail",
            "Grafana dashboard renders KPIs and model performance in real time",
            "Airflow DAG retrains model on schedule with new labelled data"
        ],
        "architecture_diagram": f"""
{data_flow}
        │
        ▼
Model Scoring Engine ({ml})
+ SHAP Explainer
        │
   ┌────┴───────────────────┐
   ▼                        ▼
Decision / Output     Audit Log (PostgreSQL)
        │
        ▼
Dashboard (Grafana)
        │
        ▼
Airflow Retraining DAG
""",
        "dataset_requirements": [
            f"Minimum 12 months of historical {domain} operational data",
            "Labelled outcome data for supervised learning tasks",
            "Feature data aligned to the business process trigger",
            "Data quality baseline — completeness ≥ 95%, freshness SLA defined",
            "Test/validation holdout set — temporally split (not random) to avoid leakage"
        ],
        "model_details": {
            "algorithm": ml,
            "training": "80/10/10 train/validation/test split (temporal). Cross-validation with time-series aware folds. Hyperparameter tuning via Optuna. MLflow experiment tracking.",
            "evaluation_metrics": "AUC-ROC | Precision | Recall | F1 | Business KPI alignment test (e.g., cost-weighted metric)"
        },
        "integration_points": [
            f"Primary {domain} source system — data ingestion",
            "Downstream action system — automated decisions / alerts",
            "CRM / ERP — outcome feedback loop",
            "Monitoring — Evidently AI + Grafana",
            "CI/CD — GitHub Actions + MLflow model registry"
        ],
        "risks_and_mitigations": [
            {"risk": "Data quality issues in source systems", "mitigation": "Great Expectations data quality suite with pipeline-blocking checks on critical fields."},
            {"risk": "Model performance degradation over time", "mitigation": "Evidently AI drift monitoring with automated Airflow retraining trigger."},
            {"risk": "Low adoption by business users", "mitigation": "SHAP explanations in plain English; change management plan; pilot with champion users first."}
        ],
        "success_metrics": [
            value,
            "Model performance ≥ baseline by ≥10% on primary evaluation metric",
            "System uptime ≥ 99.5%",
            "Prediction latency p99 ≤ 500ms",
            "User adoption ≥ 80% of target user base within 60 days of go-live"
        ],
        "timeline_estimate": [
            {"phase": "Phase 1 — Discovery & Data Prep", "duration": "3 weeks", "deliverable": "Data audit, pipeline, feature store ready"},
            {"phase": "Phase 2 — Model Development", "duration": "4 weeks", "deliverable": "Trained model, evaluation report, SHAP integration"},
            {"phase": "Phase 3 — API & Integration", "duration": "3 weeks", "deliverable": "Scoring API, downstream integration, dashboard"},
            {"phase": "Phase 4 — UAT & Go-Live", "duration": "2 weeks", "deliverable": "UAT sign-off, production deployment, monitoring active"},
            {"phase": "Phase 5 — Optimise", "duration": "Ongoing", "deliverable": "Quarterly retraining, feature iteration, ROI review"}
        ],
        "roi_estimate": f"Implementation estimated at 3–6 months ROI payback based on: {value}. Exact figures depend on current baseline — recommend baselining in Phase 1."
    }


@app.post("/case-study", response_model=None)
def get_case_study(req: CaseStudyRequest):
    """Generate a full Phase-2 case study for a selected use case."""
    domain_key = req.domain.lower().strip()

    if domain_key not in domain_cache:
        raise HTTPException(status_code=400, detail="Domain not discovered yet. Call /discover first.")

    use_cases = domain_cache[domain_key]["use_cases"]
    match = next((uc for uc in use_cases if uc["id"] == req.use_case_id), None)

    if not match:
        raise HTTPException(status_code=404, detail=f"Use case ID {req.use_case_id} not found.")

    uc_obj = UseCaseCard(**match)

    # Try specific case study data first, fall back to generic generator
    cs_data = CASE_STUDY_DATA.get(uc_obj.title) or generate_generic_case_study(match)

    return {
        "use_case": match,
        **cs_data
    }


@app.get("/status")
def get_status():
    return {
        "status": "Running",
        "cached_domains": list(domain_cache.keys()),
        "cached_keywords": list(cache.keys()),
        "cache_size": len(cache),
        "scheduler": "Enabled"
    }


@app.get("/search", response_model=SearchResponse)
def search_use_case(q: str):
    """Legacy single-use-case search (kept for backwards compat)."""
    kw = q.lower().strip()
    if kw in cache:
        return SearchResponse(data=cache[kw]["data"], source="cache")
    raise HTTPException(status_code=404, detail=f"No cached result for '{q}'. Use /discover for domain-level search.")


if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
