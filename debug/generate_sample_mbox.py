#!/usr/bin/env python3
"""Generate sample MBOX file for testing."""

import mailbox
from datetime import datetime, timedelta
from pathlib import Path

ZOMATO_EMAIL = "orders@zomato.com"

# Sample Zomato order emails
SAMPLE_EMAILS = [
    {
        "subject": "Your Zomato order ORD123456 is confirmed",
        "from": ZOMATO_EMAIL,
        "date": "Wed, 15 Jan 2024 14:30:00 +0530",
        "body": """
Hi User,

Your order has been confirmed!

Order ID: ORD123456
Date: 15 Jan 2024, 2:30 PM

Restaurant: Dominoes Pizza
Address: MG Road, Bangalore

Items ordered:
- Margherita Pizza (Large) x1
- Garlic Bread x1
- Coke 500ml x1

Subtotal: ₹450.00
Delivery Charges: ₹40.00
Promo Discount: -₹50.00
Total Amount: ₹440.00

Payment Method: Credit Card
Status: Confirmed

Estimated delivery time: 35 minutes

Thank you for ordering with Zomato!

Best regards,
Zomato
        """
    },
    {
        "subject": "Your Zomato order ORD123457 is confirmed",
        "from": ZOMATO_EMAIL,
        "date": "Wed, 20 Jan 2024 13:15:00 +0530",
        "body": """
Hi User,

Your order has been confirmed!

Order ID: ORD123457
Date: 20 Jan 2024, 1:15 PM

Restaurant: Biryani House
Address: Koramangala, Bangalore

Items ordered:
- Chicken Biryani (2 serves) x1
- Raita x1
- Shorba x1

Subtotal: ₹650.00
Delivery Charges: ₹60.00
Promo Discount: -₹30.00
Total Amount: ₹680.00

Payment Method: Debit Card
Status: Confirmed

Estimated delivery time: 40 minutes

Thank you for ordering with Zomato!

Best regards,
Zomato
        """
    },
    {
        "subject": "Your Zomato order ORD123458 is confirmed",
        "from": ZOMATO_EMAIL,
        "date": "Wed, 25 Jan 2024 10:45:00 +0530",
        "body": """
Hi User,

Your order has been confirmed!

Order ID: ORD123458
Date: 25 Jan 2024, 10:45 AM

Restaurant: Cafe Coffee Day
Address: Indiranagar, Bangalore

Items ordered:
- Americano (Grande) x1
- Chocolate Croissant x1

Subtotal: ₹280.00
Delivery Charges: ₹20.00
Total Amount: ₹300.00

Payment Method: Wallet
Status: Confirmed

Estimated delivery time: 25 minutes

Thank you for ordering with Zomato!

Best regards,
Zomato
        """
    },
]


def generate_sample_mbox(output_file: str = "sample_zomato.mbox"):
    """Generate sample MBOX file."""
    output_path = Path(output_file)
    
    # Create MBOX file
    mbox = mailbox.mbox(str(output_path))
    
    for idx, email_data in enumerate(SAMPLE_EMAILS):
        # Create message
        from email.message import EmailMessage
        msg = EmailMessage()
        
        msg['Subject'] = email_data['subject']
        msg['From'] = email_data['from']
        msg['Date'] = email_data['date']
        msg['To'] = 'user@example.com'
        msg['Message-ID'] = f'<{idx}@zomato.com>'
        msg.set_content(email_data['body'])
        
        # Add to mbox
        mbox.add(msg)
    
    mbox.close()
    
    print(f"Sample MBOX file created: {output_path}")
    print(f"Total emails: {len(SAMPLE_EMAILS)}")
    print("\nNow you can test with:")
    print(f"  python main.py ingest {output_file} -v")


if __name__ == '__main__':
    generate_sample_mbox()
