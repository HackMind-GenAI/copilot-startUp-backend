#!/usr/bin/env python3
"""
Interactive BigQuery Analysis Test
Run this script and it will prompt you for a record ID to analyze.
"""

import sys
import os

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_bigquery_analysis import BigQueryAnalysisRunner

def interactive_test():
    """Interactive test that prompts for record ID"""
    print("🧪 Interactive BigQuery Analysis Test")
    print("=" * 50)
    
    try:
        # Ask user about data source
        print("Choose data source:")
        print("1. BigQuery (requires authentication)")
        print("2. Mock data (for testing without BigQuery)")
        
        data_choice = input("\nEnter choice (1-2): ").strip()
        use_mock = data_choice == "2"
        
        if use_mock:
            print("🧪 Using mock data mode")
        
        # Initialize the runner
        runner = BigQueryAnalysisRunner(use_mock_data=use_mock)
        
        # Get record ID from user
        if use_mock:
            record_id = input("\n📋 Enter a record ID for testing (or press Enter for 'demo_001'): ").strip()
            if not record_id:
                record_id = "demo_001"
        else:
            record_id = input("\n📋 Enter the BigQuery record ID to analyze: ").strip()
            if not record_id:
                print("❌ No record ID provided. Exiting.")
                return False
        
        print(f"\n🎯 Starting analysis for ID: {record_id}")
        
        # Run the full analysis
        success = runner.run_full_analysis(record_id)
        
        if success:
            print("\n🎉 All done! Check your BigQuery table for the updated results.")
            return True
        else:
            print("\n💔 Analysis failed. Please check the errors above.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis interrupted by user.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def demo_with_sample_id():
    """Demo function with a sample ID for testing"""
    print("🧪 Demo Analysis Test (Mock Data Mode)")
    print("=" * 50)
    
    # Use mock data to avoid authentication issues
    sample_id = "demo_001"
    
    print(f"🎯 Running demo analysis for ID: {sample_id}")
    print("🧪 Using mock data (no BigQuery authentication required)")
    
    try:
        runner = BigQueryAnalysisRunner(use_mock_data=True)
        success = runner.run_full_analysis(sample_id)
        
        if success:
            print(f"\n✅ Demo completed successfully for ID: {sample_id}")
        else:
            print(f"\n❌ Demo failed for ID: {sample_id}")
        
        return success
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 BigQuery Analysis Test Suite")
    print("=" * 50)
    print("Choose an option:")
    print("1. Interactive test (choose BigQuery or mock data)")
    print("2. Demo with mock data (no authentication required)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        interactive_test()
    elif choice == "2":
        demo_with_sample_id()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice. Please run the script again.")
