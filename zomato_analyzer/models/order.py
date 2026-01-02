"""Order data model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """Represents a Zomato order."""
    order_id: str
    date: datetime
    restaurant_name: str
    amount: float
    delivery_fee: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    status: str = "completed"  # completed, cancelled, refunded
    payment_method: Optional[str] = None
    delivery_location: Optional[str] = None
    order_items: Optional[str] = None  # JSON or string representation
    raw_email_body: Optional[str] = None  # For debugging/reference
    email_date: Optional[datetime] = None
    
    @property
    def year(self) -> int:
        """Extract year from order date."""
        return self.date.year
    
    @property
    def month(self) -> int:
        """Extract month from order date."""
        return self.date.month
    
    @property
    def month_year(self) -> str:
        """Return month-year string."""
        return self.date.strftime("%Y-%m")
