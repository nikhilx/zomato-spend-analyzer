# Extension Guide

This document explains how to extend the Zomato Analyzer for additional features.

## Adding Refund Tracking

Refunds are a common occurrence with food delivery apps. Here's how to add refund support:

### Step 1: Update the Order Model

Edit [zomato_analyzer/models/order.py](zomato_analyzer/models/order.py):

```python
@dataclass
class Order:
    # ... existing fields ...
    refund_amount: float = 0.0
    refund_date: Optional[datetime] = None
    refund_reason: Optional[str] = None
    is_refunded: bool = False
```

### Step 2: Update Database Schema

Edit [zomato_analyzer/db/database.py](zomato_analyzer/db/database.py) in `init_db()`:

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        ...existing columns...
        refund_amount REAL DEFAULT 0,
        refund_date TEXT,
        refund_reason TEXT,
        is_refunded BOOLEAN DEFAULT 0
    )
""")
```

Update `insert_order()` and `_row_to_order()` methods to handle new fields.

### Step 3: Add Refund Extraction

Edit [zomato_analyzer/parsers/zomato.py](zomato_analyzer/parsers/zomato.py):

```python
class ZomatoEmailParser:
    REFUND_PATTERN = r'Refunded:\s*(?:₹|Rs\.?)\s*([\d,]+\.?\d*)'
    REFUND_DATE_PATTERN = r'Refund date:\s*([^\n]+)'
    
    @staticmethod
    def _extract_refund_info(body: str) -> tuple:
        """Extract refund amount and date."""
        refund_amount = 0.0
        refund_date = None
        
        match = re.search(ZomatoEmailParser.REFUND_PATTERN, body)
        if match:
            refund_amount = float(match.group(1).replace(',', ''))
        
        match = re.search(ZomatoEmailParser.REFUND_DATE_PATTERN, body)
        if match:
            date_str = match.group(1).strip()
            refund_date = datetime.strptime(date_str, '%d %b %Y')
        
        return refund_amount, refund_date
```

### Step 4: Add Refund Analytics

Edit [zomato_analyzer/analytics/queries.py](zomato_analyzer/analytics/queries.py):

```python
class OrderAnalytics:
    def get_total_refunds(self) -> float:
        """Get total amount refunded."""
        orders = self.db.get_all_orders()
        return sum(order.refund_amount for order in orders if order.is_refunded)
    
    def get_refund_rate(self) -> float:
        """Get percentage of orders refunded."""
        total = self.get_total_orders()
        if total == 0:
            return 0.0
        refunded = len([o for o in self.db.get_all_orders() if o.is_refunded])
        return (refunded / total) * 100
```

## Adding Swiggy Support

Swiggy is another popular food delivery service. Here's how to add support:

### Step 1: Create Swiggy Parser

Create [zomato_analyzer/parsers/swiggy.py](zomato_analyzer/parsers/swiggy.py):

```python
"""Swiggy email parser."""
import re
from datetime import datetime
from typing import Optional

from zomato_analyzer.models.order import Order


class SwiggyEmailParser:
    """Parser for Swiggy order confirmation emails."""
    
    ORDER_ID_PATTERN = r'Order ID:\s*#?([A-Z0-9]+)'
    RESTAURANT_PATTERN = r'Restaurant:\s*([^\n]+)'
    TOTAL_AMOUNT_PATTERN = r'Total:\s*(?:₹|Rs\.?)\s*([\d,]+\.?\d*)'
    
    @staticmethod
    def extract_order(subject: str, from_addr: str, body: str,
                     email_date: Optional[datetime] = None) -> Optional[Order]:
        """Extract order from Swiggy email."""
        # Similar implementation to ZomatoEmailParser
        # Adjust regex patterns for Swiggy email format
        pass
```

### Step 2: Update MBox Validator

Edit [zomato_analyzer/parsers/mbox_parser.py](zomato_analyzer/parsers/mbox_parser.py):

```python
@staticmethod
def validate_email(subject: str, from_addr: str) -> bool:
    """Check if email is from food delivery service."""
    food_delivery_indicators = [
        'zomato' in subject.lower() or 'zomato' in from_addr.lower(),
        'swiggy' in subject.lower() or 'swiggy' in from_addr.lower(),
    ]
    return any(food_delivery_indicators)
```

### Step 3: Update Main Entry Point

Edit [main.py](main.py) to use appropriate parser:

```python
from zomato_analyzer.parsers.swiggy import SwiggyEmailParser

def _process_email(subject: str, from_addr: str, body: str, db: OrderDatabase) -> tuple:
    """Process email with appropriate parser."""
    email_date = None
    try:
        email_date = parsedate_to_datetime(from_addr)
    except Exception:
        pass
    
    # Try Zomato parser first
    order = ZomatoEmailParser.extract_order(subject, from_addr, body, email_date)
    
    # Fallback to Swiggy if Zomato fails
    if not order:
        order = SwiggyEmailParser.extract_order(subject, from_addr, body, email_date)
    
    if order:
        if db.insert_order(order, upsert=True):
            return True, f"✓ {order.order_id}: {order.restaurant_name}"
    
    return False, f"Failed to parse: {subject}"
```

## Adding Gmail API Integration

Instead of MBOX files, fetch directly from Gmail:

### Step 1: Create Gmail Parser

Create [zomato_analyzer/parsers/gmail.py](zomato_analyzer/parsers/gmail.py):

```python
"""Gmail API integration for fetching Zomato emails."""
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth.oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery


class GmailParser:
    """Fetch emails from Gmail API."""
    
    def __init__(self, credentials_file: str):
        """Initialize Gmail API client."""
        self.service = self._get_gmail_service(credentials_file)
    
    def _get_gmail_service(self, credentials_file: str):
        """Authenticate and return Gmail service."""
        # Implement OAuth2 flow or service account authentication
        pass
    
    def fetch_zomato_emails(self):
        """Fetch all Zomato emails from Gmail."""
        results = self.service.users().messages().list(
            userId='me',
            q='from:zomato@zomato.com OR subject:Zomato'
        ).execute()
        
        messages = results.get('messages', [])
        
        for message in messages:
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id']
            ).execute()
            
            yield msg['payload']['headers'], msg['payload']['body']
```

### Step 2: Add CLI Command

Update [main.py](main.py):

```python
# Add new command
gmail_parser = subparsers.add_parser('ingest-gmail', 
                                     help='Ingest from Gmail API')
gmail_parser.add_argument('credentials', help='Path to credentials JSON')
gmail_parser.add_argument('-v', '--verbose', action='store_true')

# In main():
elif args.command == 'ingest-gmail':
    ingest_gmail(args.credentials, db, args.verbose)
```

## Best Practices for Extensions

1. **Keep parsers isolated**: Each food service should have its own parser module
2. **Reuse data models**: Use the same Order class for all services
3. **Update analytics together**: When adding new fields, update analytics methods
4. **Test idempotency**: Ensure re-running doesn't create duplicates
5. **Document patterns**: Add regex patterns as comments for maintainability
6. **Use feature flags**: Consider config options for enabling/disabling features

## Common Regex Patterns

Zomato and Swiggy emails use similar formats. Common patterns:

```regex
# Order IDs (usually alphanumeric)
Order ID:?\s*#?([A-Z0-9]+)

# Currency amounts (Indian Rupees)
(?:₹|Rs\.?)\s*([\d,]+\.?\d*)

# Dates (multiple formats)
\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}
\d{4}-\d{2}-\d{2}
\d{1,2}/\d{1,2}/\d{4}

# Email addresses
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
```

## Database Migrations

When updating the schema:

1. Add new columns to existing table
2. Set appropriate defaults
3. Update `_row_to_order()` to handle new fields
4. Update `insert_order()` to write new fields

Example:

```python
# In init_db()
cursor.execute("ALTER TABLE orders ADD COLUMN new_field TEXT DEFAULT NULL")

# In insert_order()
# Add new_field to the UPDATE and INSERT queries

# In _row_to_order()
new_field=row['new_field'] if 'new_field' in row.keys() else None
```

Note: SQLite doesn't enforce schema strictly, but it's good practice to keep schema and code in sync.

