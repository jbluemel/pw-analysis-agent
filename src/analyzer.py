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

# DSPy Module (the agent)

class AuctionAnalyzer(dspy.Module):
    def __init__(self, db: AuctionDatabase):
        super().__init__()
        self.db = db
        self.analyze_category = dspy.ChainOfThought(AnalyzeCategory)
        self.compare_categories = dspy.ChainOfThought(CompareCategories)
    
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
