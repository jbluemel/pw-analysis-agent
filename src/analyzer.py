import dspy
from src.database import AuctionDatabase
from typing import Dict, List, Optional

# DSPy Signatures

class AnalyzeData(dspy.Signature):
    """Analyze auction data and provide insights."""
    
    data = dspy.InputField(desc="Data to analyze (from database query)")
    context = dspy.InputField(desc="What this data represents and what to look for")
    insights = dspy.OutputField(desc="Key insights, patterns, and observations")

class CompareData(dspy.Signature):
    """Compare two datasets and identify differences."""
    
    dataset1 = dspy.InputField(desc="First dataset with label")
    dataset2 = dspy.InputField(desc="Second dataset with label")
    comparison = dspy.OutputField(desc="Key differences and comparative insights")

class InvestigateAnomaly(dspy.Signature):
    """Investigate why a metric is unusual."""
    
    anomaly_description = dspy.InputField(desc="The unusual metric or pattern observed")
    supporting_data = dspy.InputField(desc="Additional data to help explain the anomaly")
    explanation = dspy.OutputField(desc="Likely explanations for the anomaly")

class GenerateReport(dspy.Signature):
    """Generate an executive summary report."""
    
    analyses = dspy.InputField(desc="Collection of analyses performed")
    report = dspy.OutputField(desc="Executive summary with key findings and recommendations")


class AuctionAnalyzer(dspy.Module):
    """Generic auction data analyzer using flexible database queries."""
    
    def __init__(self, db: AuctionDatabase):
        super().__init__()
        self.db = db
        
        # DSPy modules
        self.analyze = dspy.ChainOfThought(AnalyzeData)
        self.compare = dspy.ChainOfThought(CompareData)
        self.investigate = dspy.ChainOfThought(InvestigateAnomaly)
        self.report = dspy.ChainOfThought(GenerateReport)
    
    def get_tables(self) -> List[str]:
        """Return available tables for analysis."""
        return self.db.list_tables()
    
    def get_schema(self, table_name: str) -> List[Dict]:
        """Return schema for a table."""
        return self.db.describe_table(table_name)
    
    def query(self, sql: str) -> List[Dict]:
        """Execute a query and return results."""
        return self.db.query(sql)
    
    def format_results(self, results: List[Dict], max_rows: int = 20) -> str:
        """Format query results as readable text for LLM."""
        if not results:
            return "No data returned."
        
        # Get column names from first row
        columns = list(results[0].keys())
        
        # Format as text table
        lines = []
        lines.append(" | ".join(columns))
        lines.append("-" * len(lines[0]))
        
        for row in results[:max_rows]:
            values = []
            for col in columns:
                val = row[col]
                if isinstance(val, float):
                    values.append(f"{val:,.2f}")
                elif isinstance(val, int):
                    values.append(f"{val:,}")
                else:
                    values.append(str(val))
            lines.append(" | ".join(values))
        
        if len(results) > max_rows:
            lines.append(f"... ({len(results) - max_rows} more rows)")
        
        return "\n".join(lines)
    
    # ========== ANALYSIS METHODS ==========
    
    def analyze_weekly_summary(self, fiscal_year: int = 2026) -> str:
        """Analyze overall weekly performance."""
        
        print(f"Analyzing weekly summary for FY{fiscal_year}...")
        
        results = self.query(f"""
            SELECT fiscal_week_number, total_items_sold, avg_lot_value, 
                   total_contract_price, auction_revenue,
                   pct_items_under_500, pct_items_10k_plus
            FROM weekly_metrics_summary
            WHERE fiscal_year = {fiscal_year}
            ORDER BY fiscal_week_number
        """)
        
        data_text = self.format_results(results)
        
        context = f"""
This is weekly auction performance data for fiscal year {fiscal_year}.
Key metrics:
- total_items_sold: Number of items sold that week
- avg_lot_value: Average sale price per item
- total_contract_price: Total revenue from sales
- auction_revenue: Purple Wave's revenue (fees)
- pct_items_under_500: Percentage of low-value items
- pct_items_10k_plus: Percentage of high-value items

Look for: trends over time, unusual weeks, patterns in high/low value mix.
"""
        
        result = self.analyze(data=data_text, context=context)
        return result.insights
    
    def analyze_by_dimension(self, dimension: str, fiscal_year: int = 2026) -> str:
        """Analyze performance by a specific dimension (industry, category, region, etc.)."""
        
        # Map dimension to table and column
        dimension_map = {
            'industry': ('weekly_metrics_by_industry', 'taxonomy_industry'),
            'category': ('weekly_metrics_by_category', 'taxonomy_category'),
            'family': ('weekly_metrics_by_family', 'taxonomy_family'),
            'business_category': ('weekly_metrics_by_business_category', 'business_category'),
            'region': ('weekly_metrics_by_region', 'item_region_name'),
            'district': ('weekly_metrics_by_district', 'item_district_id'),
            'territory': ('weekly_metrics_by_territory', 'item_territory_id'),
        }
        
        if dimension not in dimension_map:
            return f"Unknown dimension: {dimension}. Available: {list(dimension_map.keys())}"
        
        table, column = dimension_map[dimension]
        
        print(f"Analyzing by {dimension} for FY{fiscal_year}...")
        
        # Aggregate across weeks to see overall performance by dimension
        results = self.query(f"""
            SELECT {column}, 
                   SUM(total_items_sold) as total_items,
                   ROUND(AVG(avg_lot_value)::numeric, 2) as avg_lot_value,
                   SUM(total_contract_price) as total_revenue,
                   SUM(auction_revenue) as pw_revenue
            FROM {table}
            WHERE fiscal_year = {fiscal_year}
            GROUP BY {column}
            ORDER BY total_items DESC
        """)
        
        data_text = self.format_results(results)
        
        context = f"""
This is auction performance broken down by {dimension} for FY{fiscal_year}.
Each row represents a different {dimension} with aggregated metrics across all weeks.

Look for: which {dimension}s drive the most volume, which have highest avg values,
any surprising patterns in the mix.
"""
        
        result = self.analyze(data=data_text, context=context)
        return result.insights
    
    def investigate_week(self, week_number: int, fiscal_year: int = 2026) -> str:
        """Deep dive into a specific week to understand what drove its performance."""
        
        print(f"Investigating Week {week_number} of FY{fiscal_year}...")
        
        # Get the week's summary
        summary = self.query(f"""
            SELECT * FROM weekly_metrics_summary
            WHERE fiscal_year = {fiscal_year} AND fiscal_week_number = {week_number}
        """)
        
        # Get breakdown by industry for that week
        by_industry = self.query(f"""
            SELECT taxonomy_industry, total_items_sold, avg_lot_value, total_contract_price
            FROM weekly_metrics_by_industry
            WHERE fiscal_year = {fiscal_year} AND fiscal_week_number = {week_number}
            ORDER BY total_contract_price DESC
        """)
        
        # Get comparison to average week
        avg_week = self.query(f"""
            SELECT AVG(total_items_sold) as avg_items,
                   AVG(avg_lot_value) as avg_lot_value,
                   AVG(total_contract_price) as avg_revenue
            FROM weekly_metrics_summary
            WHERE fiscal_year = {fiscal_year}
        """)
        
        anomaly_desc = f"""
Week {week_number} Summary:
{self.format_results(summary)}

Compared to average week:
{self.format_results(avg_week)}
"""
        
        supporting = f"""
Week {week_number} breakdown by industry:
{self.format_results(by_industry)}
"""
        
        result = self.investigate(
            anomaly_description=anomaly_desc,
            supporting_data=supporting
        )
        return result.explanation
    
    def compare_dimensions(self, dim1_name: str, dim1_value: str, 
                          dim2_name: str, dim2_value: str,
                          fiscal_year: int = 2026) -> str:
        """Compare two specific dimension values (e.g., Construction vs Ag Equipment)."""
        
        dimension_map = {
            'industry': ('weekly_metrics_by_industry', 'taxonomy_industry'),
            'category': ('weekly_metrics_by_category', 'taxonomy_category'),
            'region': ('weekly_metrics_by_region', 'item_region_name'),
        }
        
        if dim1_name not in dimension_map:
            return f"Unknown dimension: {dim1_name}"
        
        table, column = dimension_map[dim1_name]
        
        print(f"Comparing {dim1_value} vs {dim2_value}...")
        
        data1 = self.query(f"""
            SELECT fiscal_week_number, total_items_sold, avg_lot_value, total_contract_price
            FROM {table}
            WHERE fiscal_year = {fiscal_year} AND {column} = '{dim1_value}'
            ORDER BY fiscal_week_number
        """)
        
        data2 = self.query(f"""
            SELECT fiscal_week_number, total_items_sold, avg_lot_value, total_contract_price
            FROM {table}
            WHERE fiscal_year = {fiscal_year} AND {column} = '{dim2_value}'
            ORDER BY fiscal_week_number
        """)
        
        result = self.compare(
            dataset1=f"{dim1_value}:\n{self.format_results(data1)}",
            dataset2=f"{dim2_value}:\n{self.format_results(data2)}"
        )
        return result.comparison
    
    def generate_weekly_report(self, fiscal_year: int = 2026) -> str:
        """Generate comprehensive weekly performance report."""
        
        print(f"Generating full report for FY{fiscal_year}...")
        
        # Gather multiple analyses
        summary_analysis = self.analyze_weekly_summary(fiscal_year)
        industry_analysis = self.analyze_by_dimension('industry', fiscal_year)
        
        # Find the unusual week (Week 9 based on data we saw)
        week9_investigation = self.investigate_week(9, fiscal_year)
        
        all_analyses = f"""
WEEKLY TREND ANALYSIS:
{summary_analysis}

INDUSTRY BREAKDOWN:
{industry_analysis}

WEEK 9 INVESTIGATION (lowest avg lot value):
{week9_investigation}
"""
        
        result = self.report(analyses=all_analyses)
        return result.report
