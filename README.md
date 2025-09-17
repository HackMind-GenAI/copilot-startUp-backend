# copilot-startUp-backend

A FastAPI-based backend service for startup analysis and consultation, featuring AI-powered metrics generation and critical analysis capabilities.

## Features

- **Startup Analysis** (`/analyze`): Generate metrics and evaluation criteria for startup investments
- **Devil's Advocate Analysis** (`/getDevilsAdvocate`): Get critical analysis, risk assessment, and alternative perspectives using LangChain Google AI agents
- **Competitor Analysis** (`/getComparisonData`): Comprehensive market research and competitor analysis with web search capabilities using LangChain agents
- **GCS Event Handling** (`/test-event`): Process Google Cloud Storage events for file analysis

## API Endpoints

### POST /analyze
Analyze startup ideas and generate investment metrics.
```json
{
  "name": "Your startup description"
}
```

### POST /getDevilsAdvocate
Get comprehensive Devil's Advocate analysis using LangChain agents.
```json
{
  "message": "The idea or statement to analyze",
  "startup_idea": "Optional context about your startup"
}
```

**Response:**
```json
{
  "counter_argument": "Critical counter-arguments to the idea",
  "risk_assessment": "Detailed risk analysis and challenges", 
  "alternative_perspective": "Alternative viewpoints and approaches"
}
```

### POST /getComparisonData
Get comprehensive competitor analysis and market research using LangChain agents with web search capabilities.
```json
{
  "company_name": "Your company name",
  "industry": "Your industry sector",
  "business_model": "Optional business model description",
  "location": "Optional company location", 
  "target_market": "Optional target market description"
}
```

**Response:**
```json
{
  "industry_overview": "Comprehensive industry analysis and market insights",
  "market_size": "Market size estimates and growth projections",
  "key_competitors": [
    {
      "name": "Competitor name",
      "valuation": "Valuation information",
      "revenue": "Revenue details",
      "profitability_status": "Profitability analysis",
      "funding_rounds": "Funding history",
      "key_metrics": "Performance metrics",
      "competitive_advantages": "Competitive positioning"
    }
  ],
  "market_trends": "Key market trends and growth drivers",
  "investment_landscape": "Funding patterns and investor insights",
  "benchmarking_insights": "Detailed competitor analysis",
  "recommendations": "Strategic recommendations for investors"
}
```

### POST /test-event
Handle Google Cloud Storage events for document processing.

## Project Structure

```
copilot-startUp-backend/
├── main.py                     # FastAPI application
├── models/
│   └── summarize.py           # Pydantic models for request/response
├── services/
│   ├── metrics_generator.py   # Business logic and AI integration
│   ├── devils_advocate.py     # LangChain agent for critical analysis
│   └── comparison_analysis.py # LangChain agent for competitor research
├── requirements.txt            # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md                 # This file
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- Google AI API key for LangChain
- Google Cloud credentials (optional, for GCS features)

3. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

4. View API documentation at `http://localhost:8000/docs`

## Services

- **metrics_generator.py**: Core startup analysis using Google Generative AI
- **devils_advocate.py**: Critical analysis service using LangChain agents with multiple tools for comprehensive risk evaluation
- **comparison_analysis.py**: Competitor research service using LangChain agents with web search capabilities and intelligent fallback

## Technologies

- FastAPI - Web framework
- LangChain with Google Generative AI - Core AI functionality
- LangChain Community - Web search and additional tools
- DuckDuckGo Search - Real-time web search capabilities
- Pydantic - Data validation and serialization
- Google Cloud Storage (optional) - File processing
- LangSmith - Agent tracing and debugging