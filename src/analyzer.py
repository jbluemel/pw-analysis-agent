import dspy
from src.database import AuctionDatabase
from typing import Dict, List

# DSPy Signatures (define what the LLM should do)

class AnalyzeCategory(dspy.Signature):
    """Analyze auction category performance and provide insights."""
    
    category_stats = dspy.InputField(desc="Statistics for the category")
    sample_items = dspy.InputField(desc="Sample auction items from the category")
    insights = dspy.OutputField(desc="Key insights and observations about the category")

class CompareCategories(dspy.Signature):
    """Compare performance between different auction categories."""
    
    category1_analysis = dspy.InputField(desc="Analysis of first category")
    category2_analysis = dspy.InputField(desc="Analysis of second category")
    comparison = dspy.OutputField(desc="Comparative insights between categories")

# NEW: Weekly Analysis Signatures

class AnalyzeWeeklyTrends(dspy.Signature):
    """Analyze weekly auction trends and identify patterns."""
    
    weekly_data = dspy.InputField(desc="Weekly metrics data including lot values, revenue, items sold")
    summary_stats = dspy.InputField(desc="Overall statistics for the fiscal year")
    insights = dspy.OutputField(desc="Trend analysis, patterns, and key observations")

class IdentifyAnomalies(dspy.Signature):
    """Identify unusual weeks or anomalies in auction performance."""
    
    weekly_data = dspy.InputField(desc="Weekly metrics data")
    avg_metrics = dspy.InputField(desc="Average metrics for comparison")
    anomalies = dspy.OutputField(desc="List of unusual weeks with explanations")

class GenerateWeeklyReport(dspy.Signature):
    """Generate a comprehensive weekly performance report."""
    
    trend_analysis = dspy.InputField(desc="Weekly trend analysis")
    anomaly_analysis = dspy.InputField(desc="Anomaly detection results")
    summary_stats = dspy.InputField(desc="Overall statistics")
    report = dspy.OutputField(desc="Executive summary report with recommendations")

# DSPy Module (the agent)

class AuctionAnalyzer(dspy.Module):
    def __init__(self, db: AuctionDatabase):
        super().__init__()
        self.db = db
        
        # Category analysis
        self.analyze_category = dspy.ChainOfThought(AnalyzeCategory)
        self.compare_categories = dspy.ChainOfThought(CompareCategories)
        
        # Weekly analysis
        self.analyze_trends = dspy.ChainOfThought(AnalyzeWeeklyTrends)
        self.identify_anomalies = dspy.ChainOfThought(IdentifyAnomalies)
        self.generate_report = dspy.ChainOfThought(GenerateWeeklyReport)
    
    # ========== EXISTING CATEGORY METHODS ==========
    
    def analyze_single_category(self, category: str) -> str:
        """Autonomously analyze a single category"""
        
        # Step 1: Get data
        stats = self.db.get_category_stats(category)
        items = self.db.get_items(category=category, limit=5)
        
        # Format for LLM
        stats_text = f"""
Category: {category}
Total Items: {stats['count']}
Average Price: ${stats['avg_price']:,.2f}
Price Range: ${stats['min_price']:,.2f} - ${stats['max_price']:,.2f}
Total Fees: ${stats['total_fees']:,.2f}
"""
        
        items_text = "\n".join([
            f"- {item['model']}: ${item['hammer']:,.2f} (Fees: ${item['total_fees']})"
            for item in items
        ])
        
        # Step 2: Agent analyzes autonomously
        result = self.analyze_category(
            category_stats=stats_text,
            sample_items=items_text
        )
        
        return result.insights
    
    def compare_two_categories(self, cat1: str, cat2: str) -> str:
        """Autonomously compare two categories"""
        
        # Step 1: Analyze each category
        analysis1 = self.analyze_single_category(cat1)
        analysis2 = self.analyze_single_category(cat2)
        
        # Step 2: Agent compares autonomously
        result = self.compare_categories(
            category1_analysis=f"{cat1}: {analysis1}",
            category2_analysis=f"{cat2}: {analysis2}"
        )
        
        return result.comparison
    
    def analyze_all_categories(self) -> str:
        """Autonomously analyze all categories"""
        
        categories = self.db.get_all_categories()
        
        analyses = []
        for category in categories:
            print(f"\nAnalyzing {category}...")
            analysis = self.analyze_single_category(category)
            analyses.append(f"\n{category}:\n{analysis}")
        
        return "\n".join(analyses)
    
    # ========== NEW WEEKLY ANALYSIS METHODS ==========
    
    def analyze_weekly_lot_value_trends(self, fiscal_year: int = 2026) -> str:
        """Autonomously analyze weekly average lot value trends"""
        
        print(f"Analyzing weekly trends for FY{fiscal_year}...")
        
        # Step 1: Get weekly data
        weekly_data = self.db.get_weekly_metrics(fiscal_year=fiscal_year)
        summary_stats = self.db.get_weekly_stats_summary(fiscal_year=fiscal_year)
        
        # Step 2: Format for LLM
        weekly_text = "\n".join([
            f"Week {w['fiscal_week_number']} ({w['week_start_date']} to {w['week_end_date']}): "
            f"Avg Lot Value: ${w['avg_lot_value']:,}, "
            f"Items: {w['total_items_sold']}, "
            f"Revenue: ${w['total_revenue']:,}, "
            f"Bids: {w['total_bids']}"
            for w in weekly_data
        ])
        
        summary_text = f"""
Fiscal Year {fiscal_year} Summary:
Total Weeks: {summary_stats['total_weeks']}
Overall Avg Lot Value: ${summary_stats['avg_lot_value_overall']:,.2f}
Min Weekly Avg: ${summary_stats['min_weekly_lot_value']:,}
Max Weekly Avg: ${summary_stats['max_weekly_lot_value']:,}
Total Revenue: ${summary_stats['total_revenue_fy']:,}
Total Items Sold: {summary_stats['total_items_fy']}
Total Bids: {summary_stats['total_bids_fy']}
"""
        
        # Step 3: Agent analyzes trends
        result = self.analyze_trends(
            weekly_data=weekly_text,
            summary_stats=summary_text
        )
        
        return result.insights
    
    def find_weekly_anomalies(self, fiscal_year: int = 2026) -> str:
        """Autonomously identify unusual weeks"""
        
        print(f"Identifying anomalies for FY{fiscal_year}...")
        
        # Step 1: Get data
        weekly_data = self.db.get_weekly_metrics(fiscal_year=fiscal_year)
        summary_stats = self.db.get_weekly_stats_summary(fiscal_year=fiscal_year)
        
        # Step 2: Format for LLM
        weekly_text = "\n".join([
            f"Week {w['fiscal_week_number']}: Avg Lot Value: ${w['avg_lot_value']:,}, "
            f"Items: {w['total_items_sold']}, Revenue: ${w['total_revenue']:,}"
            for w in weekly_data
        ])
        
        avg_text = f"""
Average Metrics (for comparison):
Avg Lot Value: ${summary_stats['avg_lot_value_overall']:,.2f}
Avg Items per Week: {summary_stats['total_items_fy'] / summary_stats['total_weeks']:.0f}
"""
        
        # Step 3: Agent identifies anomalies
        result = self.identify_anomalies(
            weekly_data=weekly_text,
            avg_metrics=avg_text
        )
        
        return result.anomalies
    
    def generate_full_weekly_report(self, fiscal_year: int = 2026) -> str:
        """Autonomously generate comprehensive weekly report"""
        
        print(f"Generating full report for FY{fiscal_year}...")
        
        # Step 1: Get all analyses
        trend_analysis = self.analyze_weekly_lot_value_trends(fiscal_year)
        anomaly_analysis = self.find_weekly_anomalies(fiscal_year)
        summary_stats = self.db.get_weekly_stats_summary(fiscal_year)
        
        # Step 2: Format summary stats
        summary_text = f"""
FY{fiscal_year} Performance:
- {summary_stats['total_weeks']} weeks of data
- ${summary_stats['total_revenue_fy']:,} total revenue
- {summary_stats['total_items_fy']} items sold
- ${summary_stats['avg_lot_value_overall']:,.2f} average lot value
"""
        
        # Step 3: Agent generates executive report
        result = self.generate_report(
            trend_analysis=trend_analysis,
            anomaly_analysis=anomaly_analysis,
            summary_stats=summary_text
        )
        
        return result.report