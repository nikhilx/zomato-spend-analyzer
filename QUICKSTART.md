# Quick Start Guide

## Setup

1. **Install dependencies:**
   ```bash
   cd zomato-spend-analysis
   pip install -r requirements.txt
   ```

## Getting Your MBOX File

### Option 1: Export from Gmail (Web)
1. Go to [Google Takeout](https://takeout.google.com)
2. Select "Mail"
3. Choose the account with Zomato emails
4. Download as MBOX format
5. Extract the downloaded file

### Option 2: Using Gmail API
```bash
# Coming soon - see main.py for extension point
```

## Running the Analysis

### Step 1: Ingest Your MBOX File
```bash
# Basic usage
python main.py ingest /path/to/zomato_emails.mbox

# With verbose output to see what's being extracted
python main.py ingest /path/to/zomato_emails.mbox -v

# Using a custom database location
python main.py ingest /path/to/zomato_emails.mbox -db my_data.db
```

The tool will:
- Parse the MBOX file
- Extract Zomato order information
- Create `zomato_orders.db` (SQLite database)
- Display summary statistics

### Step 2: View Statistics
```bash
# Overall summary and year-wise breakdown
python main.py stats

# Year-wise analysis only
python main.py year-wise

# Month-wise analysis for a specific year
python main.py month-wise 2024

# Top restaurants
python main.py restaurants

# Top 20 restaurants
python main.py restaurants -n 20
```

### Step 3 (Optional): Export Data
```bash
# Export all data and analytics to JSON
python main.py export analysis.json

# Can then process with other tools, create visualizations, etc.
```

## Example Session

```bash
# Step 1: Ingest emails
$ python main.py ingest ~/Downloads/Takeout/Mail/Zomato.mbox -v
Ingesting MBOX file: ~/Downloads/Takeout/Mail/Zomato.mbox
  ✓ ORD123456: Pizza Hut - ₹450.00
  ✓ ORD123457: Biryani House - ₹680.00
  ✓ ORD123458: Cafe Coffee Day - ₹280.00
...
Results:
  Inserted: 487
  Skipped: 23

============================================================
ZOMATO SPEND SUMMARY
============================================================
Total Orders:        487
Total Spent:         ₹156,420.45
Average Order Value: ₹321.42
Total Delivery Fees: ₹12,450.00
Total Discounts:     ₹8,920.00
============================================================

# Step 2: View details
$ python main.py restaurants -n 10
================================================================================
TOP 10 RESTAURANTS
================================================================================
Rank   Restaurant                               Orders     Total Spend
--------------------------------------------------------------------------------
1      Dominoes Pizza                           45         ₹19,200.00
2      KFC                                      38         ₹14,500.00
3      Pizza Hut                                35         ₹13,450.00
...
================================================================================
```

## Troubleshooting

**No orders found?**
- Check that the MBOX file actually contains Zomato emails
- Run with `-v` to see which emails are being skipped
- Zomato emails must have "zomato" in subject or from address

**Database errors?**
- Delete `zomato_orders.db` and try again
- Check file permissions on the database directory

**Parse errors for specific emails?**
- The system is designed to skip emails that don't match expected format
- Check `README.md` for regex patterns used in extraction
- Can extend patterns for different email formats

## Next Steps

- Review `README.md` for detailed documentation
- Check `zomato_analyzer/parsers/zomato.py` to customize parsing for your email format
- See `EXTENDING.md` for adding Swiggy support, refund tracking, etc.

