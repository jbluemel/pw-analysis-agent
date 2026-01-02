from datetime import datetime
from src.analyzer import AuctionAnalyzer
from src.database import AuctionDatabase
import json

class ReportGenerator:
    def __init__(self, agent: AuctionAnalyzer):
        self.agent = agent
    
    def generate_weekly_report(self) -> dict:
        """Generate comprehensive weekly auction report"""
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_type": "weekly_auction_analysis",
            "analyses": {}
        }
        
        # Analyze all categories
        print("Generating weekly report...")
        categories = self.agent.db.get_all_categories()
        
        for category in categories:
            print(f"  Analyzing {category}...")
            analysis = self.agent.analyze_single_category(category)
            
            # Get stats for the report
            stats = self.agent.db.get_category_stats(category)
            
            report["analyses"][category] = {
                "analysis": analysis,
                "stats": {
                    "count": stats["count"],
                    "avg_price": float(stats["avg_price"]),
                    "total_fees": float(stats["total_fees"])
                }
            }
        
        return report
    
    def save_report(self, report: dict, filepath: str = None):
        """Save report to file"""
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"reports/weekly_report_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved to: {filepath}")
        return filepath
