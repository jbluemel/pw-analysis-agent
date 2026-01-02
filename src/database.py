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
    
    def close(self):
        """Close database connection"""
        self.conn.close()
