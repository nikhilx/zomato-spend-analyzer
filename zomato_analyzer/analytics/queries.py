"""Analytics queries for Zomato orders."""
from collections import defaultdict
from typing import Dict, List, Tuple

from zomato_analyzer.db.database import OrderDatabase
from zomato_analyzer.models.order import Order


class OrderAnalytics:
    """Analytics for Zomato orders."""
    
    def __init__(self, db: OrderDatabase):
        """Initialize analytics."""
        self.db = db
    
    def get_total_spend(self) -> float:
        """Get total amount spent on all orders."""
        orders = self.db.get_all_orders()
        return sum(order.total_amount for order in orders)
    
    def get_total_orders(self) -> int:
        """Get total number of orders."""
        return self.db.get_order_count()
    
    def get_average_order_value(self) -> float:
        """Get average order value."""
        total = self.get_total_orders()
        if total == 0:
            return 0.0
        return self.get_total_spend() / total
    
    def get_year_wise_spend(self) -> Dict[int, float]:
        """Get spending by year."""
        orders = self.db.get_all_orders()
        year_spend = defaultdict(float)
        
        for order in orders:
            year_spend[order.year] += order.total_amount
        
        return dict(sorted(year_spend.items()))
    
    def get_year_wise_orders(self) -> Dict[int, int]:
        """Get order count by year."""
        orders = self.db.get_all_orders()
        year_count = defaultdict(int)
        
        for order in orders:
            year_count[order.year] += 1
        
        return dict(sorted(year_count.items()))
    
    def get_month_wise_spend(self, year: int) -> Dict[int, float]:
        """Get spending by month for a specific year."""
        orders = self.db.get_orders_by_year(year)
        month_spend = defaultdict(float)
        
        for order in orders:
            month_spend[order.month] += order.total_amount
        
        return dict(sorted(month_spend.items()))
    
    def get_month_wise_orders(self, year: int) -> Dict[int, int]:
        """Get order count by month for a specific year."""
        orders = self.db.get_orders_by_year(year)
        month_count = defaultdict(int)
        
        for order in orders:
            month_count[order.month] += 1
        
        return dict(sorted(month_count.items()))
    
    def get_restaurant_wise_spend(self, limit: int = 20) -> Dict[str, float]:
        """Get spending by restaurant."""
        orders = self.db.get_all_orders()
        restaurant_spend = defaultdict(float)
        
        for order in orders:
            restaurant_spend[order.restaurant_name] += order.total_amount
        
        # Sort by spending descending
        sorted_spend = sorted(restaurant_spend.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_spend[:limit])
    
    def get_restaurant_wise_orders(self, limit: int = 20) -> Dict[str, int]:
        """Get order count by restaurant."""
        orders = self.db.get_all_orders()
        restaurant_count = defaultdict(int)
        
        for order in orders:
            restaurant_count[order.restaurant_name] += 1
        
        # Sort by count descending
        sorted_count = sorted(restaurant_count.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_count[:limit])
    
    def get_top_restaurants(self, n: int = 10) -> List[Tuple[str, float, int]]:
        """Get top restaurants by spending."""
        orders = self.db.get_all_orders()
        restaurant_stats = defaultdict(lambda: {'spend': 0.0, 'count': 0})
        
        for order in orders:
            restaurant_stats[order.restaurant_name]['spend'] += order.total_amount
            restaurant_stats[order.restaurant_name]['count'] += 1
        
        # Sort by spending descending
        top = sorted(
            [(name, stats['spend'], stats['count']) 
             for name, stats in restaurant_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return top[:n]
    
    def get_monthly_spend(self) -> Dict[str, float]:
        """Get spending by month-year across all years."""
        orders = self.db.get_all_orders()
        monthly_spend = defaultdict(float)
        
        for order in orders:
            month_year = order.month_year
            monthly_spend[month_year] += order.total_amount
        
        return dict(sorted(monthly_spend.items()))
    
    def get_monthly_orders(self) -> Dict[str, int]:
        """Get order count by month-year across all years."""
        orders = self.db.get_all_orders()
        monthly_count = defaultdict(int)
        
        for order in orders:
            month_year = order.month_year
            monthly_count[month_year] += 1
        
        return dict(sorted(monthly_count.items()))
    
    def get_stats_summary(self) -> Dict[str, any]:
        """Get overall statistics summary."""
        orders = self.db.get_all_orders()
        
        if not orders:
            return {
                'total_spend': 0,
                'total_orders': 0,
                'average_order_value': 0,
                'total_delivery_fees': 0,
                'total_discounts': 0,
                'years': []
            }
        
        total_spend = self.get_total_spend()
        total_orders = self.get_total_orders()
        total_delivery_fees = sum(order.delivery_fee for order in orders)
        total_discounts = sum(order.discount for order in orders)
        
        return {
            'total_spend': round(total_spend, 2),
            'total_orders': total_orders,
            'average_order_value': round(self.get_average_order_value(), 2),
            'total_delivery_fees': round(total_delivery_fees, 2),
            'total_discounts': round(total_discounts, 2),
            'years': sorted(self.get_year_wise_spend().keys())
        }
