#!/usr/bin/env python3
"""
Comprehensive test    def __init__(self):
        # Load configuration from config file
        self.project_id = get_project_id()
        self.dataset_id = get_dataset_id()
        self.table_name = get_table_name()
        self.table_id = get_table_id()
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=self.project_id)
        
        print(f"🔗 Connected to BigQuery table: {self.table_id}")
        print(f"📋 Project: {self.project_id}")
        print(f"📊 Dataset: {self.dataset_id}")
        print(f"🗃️ Table: {self.table_name}")1. Fetches company data from BigQuery by ID
2. Runs competitor analysis
3. Runs devil's advocate analysis  
4. Updates BigQuery with both analysis results
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.cloud import bigquery
from services.comparison_analysis import (
    get_competitor_analysis,
    CompanyData,
    CompetitorResponse
)
from services.devils_advocate import (
    get_devils_advocate_analysis,
    DevilsAdvocateRequest,
    DevilsAdvocateResponse
)
from bigquery_config import (
    get_table_id,
    get_project_id,
    get_dataset_id,
    get_table_name,
    GCP_CONFIG,
    ANALYSIS_CONFIG
)
import dotenv

# Load environment variables for API keys
dotenv.load_dotenv()

class BigQueryAnalysisRunner:
    """Handles fetching data from BigQuery, running analysis, and updating results"""
    
    def __init__(self, use_mock_data=False):
        # Static BigQuery configuration
        self.project_id = "hackmind-471716"  # Replace with your actual project ID
        self.dataset_id = "hackmind"      # Replace with your actual dataset ID  
        self.table_name = "deal_data"         # Replace with your actual table name
        self.table_id = f"{self.project_id}.{self.dataset_id}.{self.table_name}"
        self.use_mock_data = use_mock_data
        
        if use_mock_data:
            print("🧪 Running in MOCK DATA mode (no BigQuery connection)")
            print(f"📋 Would connect to: {self.table_id}")
            self.bq_client = None
        else:
            # Try to initialize BigQuery client with error handling
            try:
                print("🔌 Attempting to connect to BigQuery...")
                self.bq_client = bigquery.Client(project=self.project_id)
                
                # Test the connection
                list(self.bq_client.list_datasets(max_results=1))
                
                print(f"✅ Connected to BigQuery successfully!")
                print(f"🔗 Table: {self.table_id}")
                print(f"📋 Project: {self.project_id}")
                print(f"📊 Dataset: {self.dataset_id}")
                print(f"🗃️ Table: {self.table_name}")
                
            except Exception as e:
                print(f"❌ Failed to connect to BigQuery: {str(e)}")
                print("🔧 Common solutions:")
                print("   1. Run: gcloud auth application-default login")
                print("   2. Or set: export GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account.json'")
                print("   3. Or use mock data mode for testing")
                print("\n🧪 Switching to MOCK DATA mode...")
                self.use_mock_data = True
                self.bq_client = None
    
    def get_mock_company_data(self, record_id: str) -> Dict[str, Any]:
        """Return mock company data for testing without BigQuery"""
        return {
            'id': record_id,
            'created_at': '2025-09-21 10:30:00 UTC',
            'basicInfo': json.dumps({
                "id": record_id,
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
            }),
            'metrics': json.dumps({
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
            }),
            'market': json.dumps({
                "tam": "$12.5B",
                "sam": "$3.2B",
                "som": "$450M",
                "growth_rate": "+15.3%",
                "market_share": "4.2%",
                "target_segment": "Mid-market enterprises with 100-1000 employees requiring scalable financial analytics solutions"
            }),
            'product': json.dumps({
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
            })
        }
    
    def fetch_company_data_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Fetch company data from BigQuery by ID"""
        if self.use_mock_data:
            print(f"🧪 Using mock data for ID: {record_id}")
            return self.get_mock_company_data(record_id)
        
        try:
            query = f"""
            SELECT *
            FROM `{self.table_id}`
            WHERE id = @record_id
            ORDER BY created_at DESC
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("record_id", "STRING", record_id)
                ]
            )
            
            query_job = self.bq_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if not results:
                print(f"❌ No record found with ID: {record_id}")
                return None
            
            record = dict(results[0])
            print(f"✅ Found record with ID: {record_id}")
            print(f"📅 Created at: {record.get('created_at')}")
            
            return record
            
        except Exception as e:
            print(f"❌ Error fetching data from BigQuery: {str(e)}")
            return None
    
    def parse_company_data(self, bq_record: Dict[str, Any]) -> Optional[CompanyData]:
        """Parse BigQuery record into CompanyData model"""
        try:
            # Parse JSON fields from BigQuery
            basic_info_json = bq_record.get('basicInfo')
            metrics_json = bq_record.get('metrics')
            market_json = bq_record.get('market')
            product_json = bq_record.get('product')
            
            # Parse JSON strings if they exist
            basic_info = json.loads(basic_info_json) if basic_info_json else {}
            metrics = json.loads(metrics_json) if metrics_json else {}
            market = json.loads(market_json) if market_json else {}
            product = json.loads(product_json) if product_json else {}
            
            # Create company data structure
            company_data_dict = {
                "basicInfo": basic_info,
                "metrics": metrics,
                "market": market,
                "product": product
            }
            
            # Validate and create CompanyData object
            company_data = CompanyData(**company_data_dict)
            
            print(f"📊 Parsed company data for: {company_data.basicInfo.name}")
            print(f"🏢 Sector: {company_data.basicInfo.sector}")
            if company_data.metrics and company_data.metrics.revenue:
                print(f"💰 Revenue: {company_data.metrics.revenue}")
            
            return company_data
            
        except Exception as e:
            print(f"❌ Error parsing company data: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_competitor_analysis(self, company_data: CompanyData) -> Optional[Dict[str, Any]]:
        """Run competitor analysis and return results"""
        try:
            print("\n🎯 Running Competitor Analysis...")
            print("-" * 50)
            
            result = get_competitor_analysis(company_data)
            
            print("✅ Competitor Analysis Complete!")
            print(f"📈 Found {len(result.direct_competitors)} direct competitors")
            print(f"💪 Identified {len(result.analysis.advantages)} competitive advantages")
            print(f"⚠️ Identified {len(result.analysis.challenges)} challenges")
            
            # Convert to dict for storage
            competitor_dict = result.model_dump()
            
            # Print summary
            print("\n📊 Competitor Analysis Summary:")
            for competitor in result.direct_competitors:
                print(f"  • {competitor.name}: {competitor.valuation} valuation, {competitor.growth} growth")
            
            return competitor_dict
            
        except Exception as e:
            print(f"❌ Error in competitor analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_devils_advocate_analysis(self, company_data: CompanyData) -> Optional[Dict[str, Any]]:
        """Run devil's advocate analysis and return results"""
        try:
            print("\n😈 Running Devil's Advocate Analysis...")
            print("-" * 50)
            
            # Create request with company data
            company_description = f"{company_data.basicInfo.name}: {company_data.basicInfo.description or 'AI startup'}"
            
            request = DevilsAdvocateRequest(
                message=f"Analyze the investment risks and potential issues for {company_description}",
                startup_idea=company_description,
                company_data=company_data.model_dump()
            )
            
            result = get_devils_advocate_analysis(request)
            
            print("✅ Devil's Advocate Analysis Complete!")
            print(f"🔍 Overall Risk Score: {result.risk_assessment.overall_risk_score}/10")
            print(f"📋 Found {len(result.counter_arguments)} counter-arguments")
            print(f"⚠️ Data Quality Score: {result.data_consistency.data_quality_score}/10")
            
            # Convert to dict for storage
            devils_advocate_dict = result.model_dump()
            
            # Print key insights
            print(f"\n😈 Devil's Advocate Summary:")
            print(f"  • Regulatory Risk: {result.risk_assessment.regulatory.risk_score}/10")
            print(f"  • Market Risk: {result.risk_assessment.market.risk_score}/10")
            print(f"  • Execution Risk: {result.risk_assessment.execution.risk_score}/10")
            
            return devils_advocate_dict
            
        except Exception as e:
            print(f"❌ Error in devil's advocate analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_bigquery_with_results(
        self, 
        record_id: str, 
        competitor_analysis: Optional[Dict[str, Any]] = None,
        devils_advocate_analysis: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update BigQuery record with analysis results"""
        if self.use_mock_data:
            print("\n🧪 Mock Mode: Simulating BigQuery update...")
            if competitor_analysis:
                print("  • ✅ Would save competitor analysis to 'competitors' column")
            if devils_advocate_analysis:
                print("  • ✅ Would save devil's advocate analysis to 'devils_advocate' column")
            print(f"  • ✅ Would update timestamp for record: {record_id}")
            return True
        
        try:
            print("\n💾 Updating BigQuery with analysis results...")
            
            # Build update fields
            update_fields = []
            parameters = [bigquery.ScalarQueryParameter("record_id", "STRING", record_id)]
            
            if competitor_analysis:
                update_fields.append("competitors = @competitor_analysis")
                parameters.append(
                    bigquery.ScalarQueryParameter(
                        "competitor_analysis", 
                        "STRING", 
                        json.dumps(competitor_analysis)
                    )
                )
            
            if devils_advocate_analysis:
                update_fields.append("devils_advocate = @devils_advocate_analysis")
                parameters.append(
                    bigquery.ScalarQueryParameter(
                        "devils_advocate_analysis", 
                        "STRING", 
                        json.dumps(devils_advocate_analysis)
                    )
                )
            
            # Add updated timestamp
            update_fields.append("updated_at = @updated_at")
            parameters.append(
                bigquery.ScalarQueryParameter(
                    "updated_at", 
                    "TIMESTAMP", 
                    datetime.utcnow()
                )
            )
            
            if not update_fields:
                print("⚠️ No analysis results to update")
                return False
            
            # Build and execute update query
            query = f"""
            UPDATE `{self.table_id}`
            SET {', '.join(update_fields)}
            WHERE id = @record_id
            """
            
            job_config = bigquery.QueryJobConfig(query_parameters=parameters)
            query_job = self.bq_client.query(query, job_config=job_config)
            query_job.result()  # Wait for completion
            
            print(f"✅ Successfully updated BigQuery record: {record_id}")
            
            if competitor_analysis:
                print("  • ✅ Competitor analysis saved to 'competitors' column")
            if devils_advocate_analysis:
                print("  • ✅ Devil's advocate analysis saved to 'devils_advocate' column")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating BigQuery: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_full_analysis(self, record_id: str) -> bool:
        """Run complete analysis pipeline for a given record ID"""
        print(f"🚀 Starting Full Analysis Pipeline for ID: {record_id}")
        print("=" * 70)
        
        # Step 1: Fetch data from BigQuery
        bq_record = self.fetch_company_data_by_id(record_id)
        if not bq_record:
            return False
        
        # Step 2: Parse company data
        company_data = self.parse_company_data(bq_record)
        if not company_data:
            return False
        
        # Step 3: Run competitor analysis (if enabled)
        competitor_results = None
        if ANALYSIS_CONFIG.get('run_competitor_analysis', True):
            competitor_results = self.run_competitor_analysis(company_data)
        else:
            print("\n⏭️ Skipping Competitor Analysis (disabled in config)")
        
        # Step 4: Run devil's advocate analysis (if enabled)
        devils_advocate_results = None
        if ANALYSIS_CONFIG.get('run_devils_advocate', True):
            devils_advocate_results = self.run_devils_advocate_analysis(company_data)
        else:
            print("\n⏭️ Skipping Devil's Advocate Analysis (disabled in config)")
        
        # Step 5: Update BigQuery with results (if enabled)
        if (competitor_results or devils_advocate_results) and ANALYSIS_CONFIG.get('update_bigquery', True):
            success = self.update_bigquery_with_results(
                record_id, 
                competitor_results, 
                devils_advocate_results
            )
        elif not ANALYSIS_CONFIG.get('update_bigquery', True):
            print("\n⏭️ Skipping BigQuery update (disabled in config)")
            success = True  # Consider it successful since we completed the analyses
        else:
            print("\n⚠️ No analysis results to save")
            success = False
        
        if success:
            print("\n🎉 Full Analysis Pipeline Completed Successfully!")
            print("=" * 70)
            return True
        else:
            print("\n❌ Analysis Pipeline Failed")
            print("=" * 70)
            return False


def test_analysis_by_id(record_id: str, use_mock_data: bool = False):
    """Test function to run analysis for a specific record ID"""
    try:
        runner = BigQueryAnalysisRunner(use_mock_data=use_mock_data)
        success = runner.run_full_analysis(record_id)
        
        if success:
            print(f"\n✅ Analysis completed successfully for ID: {record_id}")
        else:
            print(f"\n❌ Analysis failed for ID: {record_id}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_with_mock_data(record_id: str = "demo_001"):
    """Test function that uses mock data (no BigQuery required)"""
    print("🧪 Testing Analysis with Mock Data (No BigQuery Required)")
    print("=" * 60)
    return test_analysis_by_id(record_id, use_mock_data=True)


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) == 1:
        # No arguments - show options
        print("BigQuery Analysis Test Options:")
        print("=" * 40)
        print("1. python test_bigquery_analysis.py <RECORD_ID>")
        print("   - Run analysis with BigQuery connection")
        print("2. python test_bigquery_analysis.py mock")
        print("   - Run analysis with mock data (no BigQuery)")
        print("3. python test_bigquery_analysis.py mock <RECORD_ID>")
        print("   - Run analysis with mock data using custom ID")
        print("\nExamples:")
        print("  python test_bigquery_analysis.py comp_001")
        print("  python test_bigquery_analysis.py mock")
        print("  python test_bigquery_analysis.py mock demo_123")
        sys.exit(1)
    
    if sys.argv[1] == "mock":
        # Mock data mode
        record_id = sys.argv[2] if len(sys.argv) > 2 else "demo_001"
        success = test_analysis_with_mock_data(record_id)
    else:
        # BigQuery mode
        record_id = sys.argv[1]
        success = test_analysis_by_id(record_id)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
