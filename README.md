# 🛡️ FORMGUARD AI

### Intelligent Government Application Preflight Verification System

> **"Detect Before You Submit."**

Built for **IDEA//FORGE Online Hackathon** | Track 1: Civic Pulse, Digital Governance & Public Information

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/PROGRAMERPARTH/FORMGUARD-AI)
[![GitHub Repository](https://img.shields.io/badge/GitHub-PROGRAMERPARTH%2FFORMGUARD--AI-blue?logo=github)](https://github.com/PROGRAMERPARTH/FORMGUARD-AI)

---

## 🎯 Problem

Thousands of students in India face scholarship application delays and rejections due to preventable errors:
- Inconsistent names across certificates
- Missing mandatory documents
- Incorrect academic year information
- Mismatched personal details

**FORMGUARD AI** helps identify these issues *before* submission.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart OCR** | Extract text from PDFs and images with AI-powered field recognition |
| 🔄 **Cross-Document Verification** | Compare names, dates, and details across all certificates |
| 📚 **Government Rule-Aware RAG** | Answers grounded in official MahaDBT scheme requirements |
| 💡 **AI Explanations** | Clear, actionable explanations for every detected issue |
| 🌐 **Multilingual Support** | English, Hindi, and Marathi |
| 📄 **PDF Reports** | Downloadable verification reports with detailed findings |
| 🔒 **Privacy-First** | Aadhaar/bank masking, temporary file handling, no permanent storage |

## 🏗️ Architecture

```
formguard-ai/
├── app.py                      # Main Streamlit application
├── config.py                   # Centralized configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
│
├── pages/                      # Streamlit UI pages
│   ├── dashboard.py            # Verification metrics dashboard
│   ├── upload.py               # Scheme selection & document upload
│   ├── document_intelligence.py # OCR extraction & field review
│   ├── verification.py         # Cross-document verification results
│   ├── assistant.py            # AI correction assistant (chat)
│   └── report.py               # PDF report generation & download
│
├── modules/                    # Core backend modules
│   ├── ocr_engine.py           # PDF/image text extraction
│   ├── pdf_extractor.py        # PDF-specific extraction
│   ├── field_extractor.py      # Structured field extraction via regex
│   ├── validation_engine.py    # Deterministic cross-doc verification
│   ├── rag_pipeline.py         # FAISS-based RAG with govt knowledge
│   ├── ai_explainer.py         # LLM explanations (Gemini) + fallback
│   ├── risk_analyzer.py        # Severity classification engine
│   ├── language_assistant.py   # Multilingual UI strings
│   ├── report_generator.py     # ReportLab PDF generation
│   └── security.py             # File validation & data masking
│
├── models/
│   └── schemas.py              # Pydantic data models
│
├── utils/
│   ├── helpers.py              # Common utilities
│   └── text_normalizer.py      # Text normalization for comparison
│
├── data/
│   ├── scheme_guidelines/      # Official scheme requirement data
│   ├── sample_documents/       # Synthetic test documents
│   └── vector_store/           # FAISS index storage
│
├── tests/                      # Automated test suite
│   ├── test_validation.py      # Validation engine tests
│   ├── test_ocr.py             # Text normalization & OCR tests
│   ├── test_rag.py             # RAG pipeline tests
│   └── test_reports.py         # Report generation tests
│
└── assets/
    └── styles.css              # Custom CSS theme
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- (Optional) Tesseract OCR for image processing
- (Optional) Google Gemini API key for AI explanations

### Installation

```bash
# 1. Clone the repository
cd formguard-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY (optional)

# 5. Run the application
streamlit run app.py
```

### Without Gemini API Key

The app works without an API key. AI explanations fall back to template-based responses. All core verification (OCR, cross-document checks, RAG knowledge retrieval) works independently.

### With Gemini API Key

Add your key to `.env` for enhanced AI-powered explanations:
```
GEMINI_API_KEY=your_key_here
```

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_validation.py -v
pytest tests/test_rag.py -v
pytest tests/test_ocr.py -v
pytest tests/test_reports.py -v

# Run with coverage
pytest tests/ --cov=modules --cov=utils -v
```

## 📋 Test Cases

| # | Scenario | Expected Result |
|---|----------|----------------|
| 1 | All documents match | PASS |
| 2 | Name differs between documents | WARNING/CRITICAL |
| 3 | Required document missing | CRITICAL |
| 4 | Academic year mismatch | WARNING |
| 5 | OCR fails to extract field | MANUAL REVIEW |
| 6 | No RAG source available | "Manual verification required" |

## 🔧 Technology Stack

- **Frontend**: Streamlit + Custom CSS + Plotly
- **Backend**: Python + Pydantic
- **OCR**: PyMuPDF + Tesseract (optional)
- **AI**: Google Gemini API + LangChain
- **RAG**: Sentence Transformers + FAISS
- **Reports**: ReportLab PDF generation
- **Data**: SQLite (metadata) + Local storage

## 🌐 Supported Schemes

Currently configured:
- **MahaDBT Post-Matric Scholarship** (Maharashtra)

Extensible architecture supports adding more schemes via JSON configuration.

## 🔒 Privacy & Security

- Files validated via magic bytes (not just extension)
- Aadhaar numbers automatically masked (XXXX-XXXX-1234)
- Bank account numbers masked
- Temporary files auto-deleted after processing
- No permanent storage of uploaded documents
- API keys managed via environment variables

## ⚠️ Disclaimer

> This application provides AI-assisted document consistency and scheme-requirement checks. It is **not** an official government verification, eligibility decision, or guarantee of application approval. Always verify with official government portals and authorities.

## 📦 Deployment

### Streamlit Community Cloud

1. Push code to GitHub
2. Connect repository on [share.streamlit.io](https://share.streamlit.io)
3. Add `GEMINI_API_KEY` to Secrets
4. Deploy

### Docker (Alternative)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

## 🏆 Hackathon Demo Guide

1. **Open the app** → Show the landing page and explain the problem
2. **Select scheme** → Choose MahaDBT Post-Matric Scholarship
3. **Upload documents** → Use sample documents or prepared test PDFs
4. **Extract data** → Show OCR extraction and field review
5. **Run verification** → Demonstrate cross-document checks
6. **Show issues** → Highlight name mismatches, missing docs
7. **AI Assistant** → Ask questions about detected issues
8. **Generate report** → Download PDF report
9. **Switch language** → Show Hindi/Marathi support

## 📄 License

Built for IDEA//FORGE Hackathon. For educational and demonstration purposes.

---

**FORMGUARD AI** — *Detect Before You Submit.* 🛡️
