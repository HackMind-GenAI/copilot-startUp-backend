#!/usr/bin/env python3
"""
Test script for the enhanced competitor analysis functionality
"""

import json
from services.comparison_analysis import (
    get_competitor_analysis, 
    CompanyData, 
    BasicInfo, 
    Metrics, 
    Market, 
    Product
)

# Sample input data matching your format
sample_company_data = {
    "basicInfo": {
        "id": "comp_001",
        "name": "VentureLens Analytics",
        "description": "AI-powered investment analytics platform that transforms complex financial data into actionable insights for venture capital firms and institutional investors.",
        "founded": "2019",
        "headquarters": "San Francisco, CA",
        "sector": "fintech",
        "stage": "series-a",
        "employees": 85,
        "valuation": "$45M",
        "growth": "+120%",
        "website": "https://venturelens.ai",
        "logo": "📊"
    },
    "metrics": {
        "revenue": "$12M",
        "customers": "1,250+",
        "burn": "$850K",
        "runway": "18 months",
        "funding": "$23M",
        "grossMargin": "78%",
        "cac": "$1,250",
        "ltv": "$18,500",
        "churnRate": "3.2%",
        "nps": 67,
        "mrr": "$1M",
        "arr_growth": "145%",
        "customer_satisfaction": "92%",
        "technology_score": "9.2/10",
        "competitor_avg_satisfaction": "87%",
        "competitor_avg_tech_score": "8.5/10",
        "implementation_speed_advantage": "30%",
        "industry_avg_gross_margin": "68%",
        "competitor_avg_churn": "8.2%",
        "customer_base_difference": "3x",
        "cost_leadership_advantage": "25%"
    },
    "market": {
        "tam": "$12.5B",
        "sam": "$3.2B", 
        "som": "$450M",
        "growth_rate": "+15.3%",
        "market_share": "4.2%",
        "target_segment": "Mid-market enterprises with 100-1000 employees requiring scalable financial analytics solutions"
    },
    "product": {
        "name": "VentureLens Analytics Platform",
        "description": "An integrated AI-powered platform that transforms raw financial data into actionable investment insights through advanced machine learning, real-time analytics, and seamless integration with existing investment workflows.",
        "features": [
            "AI-powered deal sourcing and screening",
            "Real-time portfolio performance analytics", 
            "Automated due diligence report generation",
            "Risk assessment and scenario modeling",
            "Integration with 50+ data sources",
            "Mobile-first responsive design"
        ],
        "competitive_advantages": [
            "50% faster deal analysis than traditional methods",
            "30% more accurate risk predictions using proprietary ML models",
            "99.9% uptime with enterprise-grade infrastructure",
            "24/7 customer success team support"
        ],
        "development_stage": "Production Ready"
    }
}

def test_competitor_analysis():
    """Test the competitor analysis function"""
    try:
        # Convert dict to Pydantic models
        company_data = CompanyData(**sample_company_data)
        
        print("🚀 Testing Competitor Analysis...")
        print(f"Company: {company_data.basicInfo.name}")
        print(f"Sector: {company_data.basicInfo.sector}")
        print(f"Revenue: {company_data.metrics.revenue}")
        print("-" * 50)
        
        # Run competitor analysis
        result = get_competitor_analysis(company_data)
        
        print("✅ Analysis Complete!")
        print(f"Found {len(result.direct_competitors)} direct competitors")
        print(f"Identified {len(result.analysis.advantages)} advantages")
        print(f"Identified {len(result.analysis.challenges)} challenges")
        
        # Convert to dict for JSON serialization
        result_dict = result.model_dump()
        
        print("\n📊 Competitor Analysis Results:")
        print("=" * 60)
        print(json.dumps(result_dict, indent=2))
        
        return result_dict
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_competitor_analysis()
