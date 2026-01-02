"""Zomato email parser to extract order information."""
import re
from datetime import datetime
from typing import Optional
from html.parser import HTMLParser

from zomato_analyzer.models.order import Order


class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML."""
    def __init__(self):
        super().__init__()
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ' '.join(self.text)


class ZomatoEmailParser:
    """Parser for Zomato order confirmation emails."""
    
    # Patterns to extract order information (works with both plain text and HTML)
    ORDER_ID_PATTERN = r'ORDER\s+ID:?\s*#?([A-Z0-9]{5,})'
    RESTAURANT_PATTERN = r'(?:Thank you for ordering (?:from)?|from)\s+([A-Za-z0-9\s&\-,.\']+?)(?:\s+ORDER|\s+Delivered|$)'
    RESTAURANT_IN_TAGS = r'<b>([A-Za-z0-9\s&\-,.\']+?)</b>'
    # Match 'Total paid', 'Total Amount' or 'Paid ₹...' as fallback
    TOTAL_AMOUNT_PATTERN = (
        r'(?:Total\s+(?:paid|amount|bill)?|Grand\s+Total|Total\s+Amount)'
        r'[\s\w\-:]*?₹\s*([\d,]+(?:\.\d{1,2})?)'
    )
    PAID_AMOUNT_PATTERN = r'Paid[\s:]*₹\s*([\d,]+(?:\.\d{1,2})?)'
    DELIVERY_FEE_PATTERN = r'(?:Delivery\s+(?:Charges|Fee|Charge))[\s\w\-:]*?₹\s*([\d,]+\.?\d*)'
    DISCOUNT_PATTERN = r'(?:Discount|Promo)[\s\w\-:]*?₹\s*([\d,]+\.?\d*)'
    DATE_PATTERN = r'(?:Order|Ordered|Issued|31\s+Jul|[0-3]?\d\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December))[^\d]*?([0-3]?\d\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[^\d]*\d{4}[^>]*)'
    
    @staticmethod
    def extract_order(subject: str, from_addr: str, body: str, 
        email_date: Optional[datetime] = None) -> Optional[Order]:
        """
        Extract order information from Zomato email.
        
        Args:
            subject: Email subject
            from_addr: Email from address
            body: Email body content (HTML or plain text)
            email_date: Email date
            
        Returns:
            Order object if successfully parsed, None otherwise
        """
        try:
            # Convert HTML to plain text if needed
            clean_body = ZomatoEmailParser._convert_html_to_text(body)
            
            # Extract order ID from subject or body
            order_id = ZomatoEmailParser._extract_order_id(subject, clean_body)
            if not order_id:
                return None
            
            # Extract restaurant name
            restaurant_name = ZomatoEmailParser._extract_restaurant(clean_body, subject)
            if not restaurant_name:
                return None
            
            # Extract amounts
            total_amount = ZomatoEmailParser._extract_total_amount(clean_body)
            if total_amount is None:
                return None
            
            delivery_fee = ZomatoEmailParser._extract_delivery_fee(clean_body)
            discount = ZomatoEmailParser._extract_discount(clean_body)
            
            # Calculate food amount
            amount = total_amount - delivery_fee + discount
            
            # Extract order date/time
            order_date = ZomatoEmailParser._extract_order_date(clean_body, email_date)
            
            # Create Order object
            order = Order(
                order_id=order_id,
                order_date=order_date,
                restaurant_name=restaurant_name,
                amount=amount,
                delivery_fee=delivery_fee,
                discount=discount,
                total_amount=total_amount,
                status="completed",
                email_date=email_date,
                raw_email_body=clean_body[:1000]
            )
            
            return order
        
        except Exception as e:
            print(f"Error parsing Zomato email: {e}")
            return None
    
    @staticmethod
    def _convert_html_to_text(body: str) -> str:
        """Convert HTML body to plain text while preserving structure."""
        # Decode HTML entities first
        body = body.replace('&amp;', '&')
        body = body.replace('&lt;', '<')
        body = body.replace('&gt;', '>')
        body = body.replace('&quot;', '"')
        body = body.replace('&#39;', "'")
        
        # Simple HTML cleanup: replace common HTML patterns with spaces
        body = re.sub(r'<br\s*/?>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'<p[^>]*>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'</p>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'<td[^>]*>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'</td>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'<tr[^>]*>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'</tr>', ' ', body, flags=re.IGNORECASE)
        body = re.sub(r'<[^>]+>', '', body)  # Remove remaining HTML tags
        body = re.sub(r'\s+', ' ', body)  # Normalize whitespace
        return body.strip()
    
    @staticmethod
    def _extract_order_id(subject: str, body: str) -> Optional[str]:
        """Extract order ID from subject or body."""
        # Try subject first
        match = re.search(ZomatoEmailParser.ORDER_ID_PATTERN, subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try body
        match = re.search(ZomatoEmailParser.ORDER_ID_PATTERN, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try to extract from email subject (new pattern format)
        # e.g., "Your Zomato order from Restaurant Name"
        match = re.search(r'order\s+#?([A-Z0-9]+)', subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    @staticmethod
    def _extract_restaurant(body: str, subject: str = "") -> Optional[str]:
        """Extract restaurant name from body or subject."""
        # Prefer subject-based extraction for Pro Plus emails
        msub = re.search(r'pro\s+plus\s+order\s+from\s+(.+)$', subject, re.IGNORECASE)
        if msub:
            restaurant = msub.group(1).strip()
            restaurant = re.sub(r'^[\-:\s]+', '', restaurant)
            restaurant = re.sub(r'\s+', ' ', restaurant).strip()
            if 2 < len(restaurant) < 120:
                return restaurant

        # Try pattern: "Thank you for ordering from Restaurant Name"
        match = re.search(ZomatoEmailParser.RESTAURANT_PATTERN, body, re.IGNORECASE)
        if match:
            restaurant = match.group(1).strip()
            # strip leading punctuation (some templates include a leading hyphen)
            restaurant = re.sub(r'^[\-:\s]+', '', restaurant)
            restaurant = re.sub(r'\s+', ' ', restaurant).strip()
            if 2 < len(restaurant) < 120:  # Sanity check
                return restaurant
        
        # Try to extract from subject line
        # "Your Zomato order from Restaurant Name" or similar
        match = re.search(r'from\s+([A-Za-z0-9\s&\-,.\'\"]+)$', subject, re.IGNORECASE)
        if match:
            restaurant = match.group(1).strip()
            restaurant = re.sub(r'^[\-:\s]+', '', restaurant)
            restaurant = re.sub(r'\s+', ' ', restaurant).strip()
            if 2 < len(restaurant) < 120:
                return restaurant
        
        return None
    
    @staticmethod
    def _extract_total_amount(body: str) -> Optional[float]:
        body = re.sub(r'\s+', ' ', body)
        """Extract total amount from body."""
        # Fallback: look for 'Paid ₹...' which appears in Pro Plus templates
        match = re.search(ZomatoEmailParser.PAID_AMOUNT_PATTERN, body, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass
        
        # Primary pattern
        match = re.search(ZomatoEmailParser.TOTAL_AMOUNT_PATTERN, body, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass

        return None
    
    @staticmethod
    def _extract_delivery_fee(body: str) -> float:
        """Extract delivery fee from body."""
        match = re.search(ZomatoEmailParser.DELIVERY_FEE_PATTERN, body, re.IGNORECASE)
        if match:
            try:
                fee_str = match.group(1).replace(',', '')
                return float(fee_str)
            except ValueError:
                pass
        
        return 0.0
    
    @staticmethod
    def _extract_discount(body: str) -> float:
        """Extract discount from body."""
        match = re.search(ZomatoEmailParser.DISCOUNT_PATTERN, body, re.IGNORECASE)
        if match:
            try:
                discount_str = match.group(1).replace(',', '')
                return float(discount_str)
            except ValueError:
                pass
        
        return 0.0
    
    @staticmethod
    def _extract_order_date(body: str, email_date: Optional[datetime] = None) -> datetime:
        """Extract order date from body or use email date as fallback."""

        # Normalize HTML early
        body = re.sub(r'<[^>]+>', ' ', body)
        body = re.sub(r'\s+', ' ', body).strip()

        # Try detailed formats first
        match = re.search(ZomatoEmailParser.DATE_PATTERN, body, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()

            for date_format in [
                '%d %b %Y, %I:%M %p',
                '%d %B %Y, %I:%M %p',
                '%d-%m-%Y, %H:%M',
                '%d/%m/%Y, %H:%M',
                '%d %b %Y',
                '%d %B %Y',
                '%d %b %Y, %H:%M',
                '%d %B %Y, %H:%M',
                '%d %b, %I:%M %p',      # no year
                '%d %B, %I:%M %p'
            ]:
                try:
                    parsed = datetime.strptime(date_str, date_format)
                    if '%Y' not in date_format and email_date:
                        parsed = parsed.replace(year=email_date.year)
                    return parsed
                except ValueError:
                    continue

        # Simpler fallback (date only)
        simple_date_pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)'
        match = re.search(simple_date_pattern, body, re.IGNORECASE)
        if match and email_date:
            try:
                parsed = datetime.strptime(match.group(1), '%d %b')
                return parsed.replace(year=email_date.year)
            except ValueError:
                pass

        # Correct fallback
        if email_date:
            return email_date

        raise ValueError("Unable to determine order date")