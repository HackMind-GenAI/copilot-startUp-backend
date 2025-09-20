#!/usr/bin/env python3
"""
Test script for the enhanced Devil's Advocate Analysis
Demonstrates how to use the new company_data input format
"""

import json
from services.devils_advocate import (
    get_devils_advocate_analysis,
    DevilsAdvocateRequest,
    DevilsAdvocateResponse
)
from typing import Dict, Any

# Sample company data based on your input format
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
        "addressable_market_gap": "$2.8B",
        "underserved_market_share": "35%",
        "top_customer_revenue_concentration": "35%",
        "expected_irr_range": "25-35%",
        "established_players_market_share": "15%+",
        "scale_execution_target": "10x",
        "cost_leadership_advantage": "25%",
        "market_leader_share": "15.8%"
    },
    "financials": {
        "labels": ["2021", "2022", "2023", "2024", "2025 (Proj)"],
        "revenue": [2.1, 4.8, 8.2, 12.0, 18.5],
        "expenses": [3.2, 5.1, 7.8, 10.2, 14.1],
        "profit": [-1.1, -0.3, 0.4, 1.8, 4.4],
        "customers": [125, 380, 750, 1250, 2100]
    },
    "team": [
        {
            "id": "tm_001",
            "name": "Sarah Chen",
            "role": "CEO & Co-Founder",
            "background": "Former VP of Product at Goldman Sachs with 12 years in financial technology. MBA from Stanford, led 3 successful fintech exits."
        },
        {
            "id": "tm_002", 
            "name": "Michael Rodriguez",
            "role": "CTO & Co-Founder",
            "background": "Ex-Principal Engineer at Stripe, built scalable payment systems for 10M+ users. MS Computer Science from MIT."
        },
        {
            "id": "tm_003",
            "name": "Dr. Emily Watson",
            "role": "Chief Data Scientist",
            "background": "Former Head of AI at JPMorgan Chase, PhD in Machine Learning from Carnegie Mellon. Published 15+ papers on financial ML."
        }
    ],
    "equity": {
        "founders": 65,
        "employees": 15,
        "investors_previous": 12,
        "reserved_future": 8,
        "breakdown": [
            {"category": "Founders", "percentage": 65, "color": "#0f172a"},
            {"category": "Employee Stock Options", "percentage": 15, "color": "#fbbf24"},
            {"category": "Investors (Previous Rounds)", "percentage": 12, "color": "#3b82f6"},
            {"category": "Reserved for Future Funding", "percentage": 8, "color": "#10b981"}
        ]
    },
    "market": {
        "tam": "$12.5B",
        "sam": "$3.2B", 
        "som": "$450M",
        "growth_rate": "+15.3%",
        "market_share": "4.2%",
        "target_segment": "Mid-market enterprises with 100-1000 employees requiring scalable financial analytics solutions",
        "trends": [
            "Digital transformation acceleration in financial services",
            "Remote work driving demand for cloud-based analytics", 
            "Increased regulatory compliance requirements",
            "Growing need for real-time financial insights"
        ],
        "problem_statement": "Traditional financial analytics tools are fragmented, expensive, and difficult to integrate, leaving investment firms with inefficient decision-making processes and limited real-time insights."
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
    },
    "risk_factors": {
        "market_saturation": {
            "title": "Market Saturation",
            "risk": "Increased competition from established players",
            "mitigation": "Focus on niche markets and superior customer experience"
        },
        "economic_downturn": {
            "title": "Economic Downturn", 
            "risk": "Reduced customer spending during recession",
            "mitigation": "Diversified revenue streams and cost-efficient operations"
        },
        "key_person_dependency": {
            "title": "Key Person Dependency",
            "risk": "Heavy reliance on founder expertise",
            "mitigation": "Building strong management team and succession planning"
        },
        "technology_risks": {
            "title": "Technology Risks",
            "risk": "Rapid technological changes making product obsolete", 
            "mitigation": "Continuous R&D investment and agile development practices"
        }
    }
}

def test_devils_advocate_analysis():
    """
    Test the enhanced Devil's Advocate analysis with company data
    """
    try:
        print("🔎 Testing Devil's Advocate Analysis with Company Data...")
        print(f"Company: {sample_company_data['basicInfo']['name']}")
        print(f"Sector: {sample_company_data['basicInfo']['sector']}")
        print(f"Revenue: {sample_company_data['metrics']['revenue']}")
        print("-" * 50)
        
        # Create request object with company data
        request = DevilsAdvocateRequest(
            message="Analyze this fintech startup",
            company_data=sample_company_data
        )
        
        # Run devil's advocate analysis
        result = get_devils_advocate_analysis(request)
        
        print("✅ Analysis completed successfully!")
        print("\n" + "="*80)
        print("DEVIL'S ADVOCATE ANALYSIS RESULTS")
        print("="*80)
        
        # Convert to dict for easier access
        result_dict = result.model_dump()
        
        # Print restated input
        restated = result_dict.get('restated_input', {})
        print(f"\n📋 RESTATED INPUT:")
        print(f"   Founder Claim: {restated.get('founder_claim', 'N/A')}")
        print(f"   AI Restated: {restated.get('ai_restated', 'N/A')}")
        
        # Print counter arguments
        counter_args = result_dict.get('counter_arguments', [])
        print(f"\n🚨 COUNTER ARGUMENTS ({len(counter_args)} identified):")
        for i, arg in enumerate(counter_args, 1):
            print(f"   {i}. {arg.get('point', 'N/A')} [Validity: {arg.get('probability_validity', 'N/A')}]")
        
        # Print risk assessment
        risk_assessment = result_dict.get('risk_assessment', {})
        print(f"\n⚠️ RISK ASSESSMENT (Overall Score: {risk_assessment.get('overall_risk_score', 'N/A')}/10):")
        for risk_type in ['regulatory', 'privacy', 'market', 'execution']:
            risk_data = risk_assessment.get(risk_type, {})
            print(f"   {risk_type.title()}: Score {risk_data.get('risk_score', 'N/A')}/10 - {risk_data.get('description', 'N/A')}")
        
        # Print alternative perspectives
        alternatives = result_dict.get('alternative_perspectives', [])
        print(f"\n💡 ALTERNATIVE PERSPECTIVES ({len(alternatives)} suggestions):")
        for i, alt in enumerate(alternatives, 1):
            print(f"   {i}. {alt.get('strategy', 'N/A')} [Upside: {alt.get('potential_upside', 'N/A')}]")
        
        # Print data consistency
        data_consistency = result_dict.get('data_consistency_check', {})
        print(f"\n🔍 DATA CONSISTENCY (Quality Score: {data_consistency.get('data_quality_score', 'N/A')}/100):")
        print(f"   Missing Fields: {len(data_consistency.get('missing_fields', []))}")
        print(f"   Inconsistencies: {len(data_consistency.get('inconsistencies', []))}")
        
        # Print evidence strength
        evidence = result_dict.get('evidence_strength', {})
        print(f"\n📊 EVIDENCE STRENGTH (Score: {evidence.get('strength_score', 'N/A')}/10):")
        distribution = evidence.get('distribution', {})
        print(f"   Supporting: {distribution.get('supporting', 'N/A')}% | Weak: {distribution.get('weak', 'N/A')}%")
        
        # Print overall suggestion
        overall = result_dict.get('overall_suggestion', {})
        print(f"\n📝 OVERALL SUGGESTION:")
        print(f"   Investor Lens: {overall.get('investor_lens', 'N/A')}")
        print(f"   Confidence: {overall.get('confidence_score', 'N/A')}/10")
        print(f"   Red Flags: {len(overall.get('red_flag_alerts', []))}")
        
        # Print investor questions
        questions = result_dict.get('investor_questions', [])
        print(f"\n❓ INVESTOR QUESTIONS ({len(questions)} generated):")
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question}")
        
        # Print loop hole severity
        severity = result_dict.get('loop_hole_severity_index', 'N/A')
        print(f"\n🎯 LOOP HOLE SEVERITY INDEX: {severity}")
        
        print("\n" + "="*80)
        print(f"📄 Full JSON response saved to 'devils_advocate_result.json'")
        
        # Save full result to file
        with open('devils_advocate_result.json', 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        return result_dict
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_backward_compatibility():
    """
    Test that the old format still works (backward compatibility)
    """
    try:
        print("🔄 Testing backward compatibility with old format...")
        
        # Old format request (without company_data)
        request = DevilsAdvocateRequest(
            message="We're building a cloud-native workflow automation platform for enterprises",
            startup_idea="Enterprise automation SaaS"
        )
        
        # Run analysis with old format
        result = get_devils_advocate_analysis(request)
        
        print("✅ Backward compatibility confirmed - old format works!")
        result_dict = result.model_dump()
        print(f"   Restated input: {result_dict.get('restated_input', {}).get('ai_restated', 'N/A')[:100]}...")
        print(f"   Counter arguments: {len(result_dict.get('counter_arguments', []))} found")
        print(f"   Risk score: {result_dict.get('risk_assessment', {}).get('overall_risk_score', 'N/A')}/10")
        
        return result_dict
            
    except Exception as e:
        print(f"❌ Backward compatibility error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Devil's Advocate Analysis Test Suite")
    print("="*50)
    
    # Test 1: New company data format
    test_devils_advocate_analysis()
    
    print("\n" + "-"*50)
    
    # Test 2: Backward compatibility
    test_backward_compatibility()
    
    print("\n✨ Test suite completed!")
