import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

class AuctionDatabase:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="172.26.5.215",  # WSL IP
            port=5434,
            database="dbt_dev",
            user="dbt_user",
            password="dbt_password"
        )
    
    def get_items(
        self, 
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Query auction items with filters"""
        
        query = """
            SELECT 
                unique_id, model, category, auctiondate,
                hammer, contract_price, total_fees
            FROM itemsbasics
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        if min_price is not None:
            query += " AND hammer >= %s"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND hammer <= %s"
            params.append(max_price)
        
        query += " ORDER BY auctiondate DESC LIMIT %s"
        params.append(limit)
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def get_category_stats(self, category: str) -> Dict:
        """Get statistics for a category"""
        
        query = """
            SELECT 
                category,
                COUNT(*) as count,
                AVG(hammer) as avg_price,
                MIN(hammer) as min_price,
                MAX(hammer) as max_price,
                SUM(total_fees) as total_fees
            FROM itemsbasics
            WHERE category = %s
            GROUP BY category
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, [category])
            return cur.fetchone()
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories"""
        
        query = "SELECT DISTINCT category FROM itemsbasics WHERE category IS NOT NULL"
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]
    
    # NEW: Weekly Metrics Methods
    
    def get_weekly_metrics(
        self, 
        fiscal_year: Optional[int] = None,
        start_week: Optional[int] = None,
        end_week: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Query weekly metrics with optional filters"""
        
        query = """
            SELECT 
                fiscal_week_number, fiscal_year,
                week_start_date, week_end_date,
                total_items_sold, avg_lot_value,
                total_revenue, total_fees, total_bids
            FROM weekly_metrics
            WHERE 1=1
        """
        params = []
        
        if fiscal_year:
            query += " AND fiscal_year = %s"
            params.append(fiscal_year)
        
        if start_week:
            query += " AND fiscal_week_number >= %s"
            params.append(start_week)
        
        if end_week:
            query += " AND fiscal_week_number <= %s"
            params.append(end_week)
        
        query += " ORDER BY week_start_date"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def get_weekly_stats_summary(self, fiscal_year: int = 2026) -> Dict:
        """Get summary statistics for weekly metrics"""
        
        query = """
            SELECT 
                COUNT(*) as total_weeks,
                AVG(avg_lot_value) as avg_lot_value_overall,
                MIN(avg_lot_value) as min_weekly_lot_value,
                MAX(avg_lot_value) as max_weekly_lot_value,
                SUM(total_revenue) as total_revenue_fy,
                SUM(total_fees) as total_fees_fy,
                SUM(total_items_sold) as total_items_fy,
                SUM(total_bids) as total_bids_fy
            FROM weekly_metrics
            WHERE fiscal_year = %s
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, [fiscal_year])
            return cur.fetchone()
    
    def close(self):
        """Close database connection"""
        self.conn.close()