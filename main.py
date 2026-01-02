#!/usr/bin/env python3
"""Main entry point for Zomato Spend Analyzer."""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime

from zomato_analyzer.db.database import OrderDatabase
from zomato_analyzer.parsers.mbox_parser import MBoxParser
from zomato_analyzer.parsers.zomato import ZomatoEmailParser
from zomato_analyzer.analytics.queries import OrderAnalytics
import zomato_analyzer.config as config

DB_PATH_HELP = 'Database path (default: %(default)s)'


def _process_email(subject: str, from_addr: str, body: str, email_date: datetime, db: OrderDatabase) -> tuple:
    """
    Process a single email and extract order information.
    
    Returns:
        (success, message) tuple
    """

    order = ZomatoEmailParser.extract_order(subject, from_addr, body, email_date)
    
    if not order:
        return False, f"Failed to parse: {subject}"
    
    if db.insert_order(order, upsert=True):
        msg = f"[+] {order.order_id}: {order.restaurant_name} - {order.total_amount}"
        return True, msg
    
    msg = f"[~] {order.order_id}: Already exists (skipped)"
    return True, msg


def ingest_mbox(mbox_path: str, db: OrderDatabase, verbose: bool = False) -> int:
    """
    Ingest MBOX file and store orders in database.
    
    Args:
        mbox_path: Path to MBOX file
        db: OrderDatabase instance
        verbose: Print verbose output
        
    Returns:
        Number of orders inserted
    """
    parser = MBoxParser(mbox_path)
    inserted = 0
    skipped = 0
    
    print(f"Ingesting MBOX file: {mbox_path}")
    
    for subject, from_addr, body, date_header in parser.parse():
        if not MBoxParser.validate_email(subject, from_addr):
            skipped += 1
            continue

        email_date = None
        if date_header:
            try:
                email_date = parsedate_to_datetime(date_header)
            except Exception:
                pass
        
        success, message = _process_email(subject, from_addr, body, email_date, db)
        
        if success:
            inserted += 1
            if verbose:
                print(f"  {message}")
        else:
            skipped += 1
            if verbose:
                print(f"  [-] {message}")
    
    print("Results:")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped: {skipped}")
    
    return inserted


def show_stats(db: OrderDatabase):
    """Display statistics."""
    analytics = OrderAnalytics(db)
    stats = analytics.get_stats_summary()
    
    print("\n" + "="*60)
    print("ZOMATO SPEND SUMMARY".center(60))
    print("="*60)
    print(f"Total Orders:        {stats['total_orders']}")
    print(f"Total Spent:         ₹{stats['total_spend']:,.2f}")
    print(f"Average Order Value: ₹{stats['average_order_value']:,.2f}")
    print(f"Total Delivery Fees: ₹{stats['total_delivery_fees']:,.2f}")
    print(f"Total Discounts:     ₹{stats['total_discounts']:,.2f}")
    print("="*60)


def show_year_wise(db: OrderDatabase):
    """Show year-wise analytics."""
    analytics = OrderAnalytics(db)
    year_spend = analytics.get_year_wise_spend()
    year_orders = analytics.get_year_wise_orders()
    
    print("\n" + "="*60)
    print("YEAR-WISE ANALYTICS".center(60))
    print("="*60)
    print(f"{'Year':<10} {'Orders':<15} {'Total Spend':<20} {'Avg/Order':<15}")
    print("-"*60)
    
    for year in year_spend.keys():
        orders = year_orders.get(year, 0)
        spend = year_spend.get(year, 0)
        avg = spend / orders if orders > 0 else 0
        print(f"{year:<10} {orders:<15} ₹{spend:>17,.2f} ₹{avg:>13,.2f}")
    
    print("="*60)


def show_month_wise(db: OrderDatabase, year: int):
    """Show month-wise analytics for a specific year."""
    analytics = OrderAnalytics(db)
    month_spend = analytics.get_month_wise_spend(year)
    month_orders = analytics.get_month_wise_orders(year)
    
    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    
    print("="*60)
    print(f"MONTHLY ANALYTICS - {year}".center(60))
    print("="*60)
    print(f"{'Month':<10} {'Orders':<15} {'Total Spend':<20} {'Avg/Order':<15}")
    print("-"*60)
    
    for month in range(1, 13):
        if month in month_spend:
            orders = month_orders.get(month, 0)
            spend = month_spend.get(month, 0)
            avg = spend / orders if orders > 0 else 0
            month_name = month_names[month]
            print(f"{month_name:<10} {orders:<15} ₹{spend:>17,.2f} ₹{avg:>13,.2f}")
    
    print("="*60)


def show_restaurant_wise(db: OrderDatabase, limit: int = 15):
    """Show restaurant-wise analytics."""
    analytics = OrderAnalytics(db)
    top_restaurants = analytics.get_top_restaurants(limit)
    
    print("="*80)
    print(f"TOP {limit} RESTAURANTS".center(80))
    print("="*80)
    print(f"{'Rank':<6} {'Restaurant':<40} {'Orders':<10} {'Total Spend':<20}")
    print("-"*80)
    
    for idx, (name, spend, count) in enumerate(top_restaurants, 1):
        display_name = name[:37] + "..." if len(name) > 40 else name
        print(f"{idx:<6} {display_name:<40} {count:<10} ₹{spend:>17,.2f}")
    
    print("="*80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Zomato Spend Analysis Tool",
        epilog="Examples:\n"
          "  python main.py ingest zomato_emails.mbox\n"
          "  python main.py stats\n"
          "  python main.py year-wise\n"
          "  python main.py month-wise 2024\n"
          "  python main.py restaurants",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest MBOX file')
    ingest_parser.add_argument('mbox_file', help='Path to MBOX file')
    ingest_parser.add_argument('-v', '--verbose', action='store_true', 
                              help='Verbose output')
    ingest_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                              help=DB_PATH_HELP)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show overall statistics')
    stats_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                             help=DB_PATH_HELP)
    
    # Year-wise command
    year_parser = subparsers.add_parser('year-wise', help='Show year-wise analytics')
    year_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                            help=DB_PATH_HELP)
    
    # Month-wise command
    month_parser = subparsers.add_parser('month-wise', help='Show month-wise analytics')
    month_parser.add_argument('year', type=int, help='Year to analyze')
    month_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                             help=DB_PATH_HELP)
    
    # Restaurants command
    rest_parser = subparsers.add_parser('restaurants', help='Show restaurant-wise analytics')
    rest_parser.add_argument('-n', '--limit', type=int, default=15,
                            help='Number of restaurants to show (default: %(default)s)')
    rest_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                            help=DB_PATH_HELP)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to JSON')
    export_parser.add_argument('output_file', help='Output JSON file path')
    export_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                              help=DB_PATH_HELP)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    db = OrderDatabase(args.database)
    
    try:
        if args.command == 'ingest':
            ingest_mbox(args.mbox_file, db, args.verbose)
            show_stats(db)
        
        elif args.command == 'stats':
            show_stats(db)
            show_year_wise(db)
        
        elif args.command == 'year-wise':
            show_year_wise(db)
        
        elif args.command == 'month-wise':
            show_month_wise(db, args.year)
        
        elif args.command == 'restaurants':
            show_restaurant_wise(db, args.limit)
        
        elif args.command == 'export':
            analytics = OrderAnalytics(db)
            orders = db.get_all_orders()
            
            data = {
                'summary': analytics.get_stats_summary(),
                'year_wise_spend': analytics.get_year_wise_spend(),
                'year_wise_orders': analytics.get_year_wise_orders(),
                'top_restaurants': [
                    {
                        'restaurant': name,
                        'total_spend': spend,
                        'order_count': count
                    }
                    for name, spend, count in analytics.get_top_restaurants(100)
                ],
                'orders': [
                    {
                        'order_id': o.order_id,
                        'order_date': o.order_date.isoformat(),
                        'restaurant': o.restaurant_name,
                        'total_amount': o.total_amount,
                        'delivery_fee': o.delivery_fee,
                        'discount': o.discount
                    }
                    for o in orders
                ]
            }
            
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Data exported to {output_path}")
    
    finally:
        db.close()


if __name__ == '__main__':
    main()



def show_stats(db: OrderDatabase):
    """Display statistics."""
    analytics = OrderAnalytics(db)
    stats = analytics.get_stats_summary()
    
    print("\n" + "="*60)
    print("ZOMATO SPEND SUMMARY".center(60))
    print("="*60)
    print(f"Total Orders:        {stats['total_orders']}")
    print(f"Total Spent:         ₹{stats['total_spend']:,.2f}")
    print(f"Average Order Value: ₹{stats['average_order_value']:,.2f}")
    print(f"Total Delivery Fees: ₹{stats['total_delivery_fees']:,.2f}")
    print(f"Total Discounts:     ₹{stats['total_discounts']:,.2f}")
    print("="*60)


def show_year_wise(db: OrderDatabase):
    """Show year-wise analytics."""
    analytics = OrderAnalytics(db)
    year_spend = analytics.get_year_wise_spend()
    year_orders = analytics.get_year_wise_orders()
    
    print("\n" + "="*60)
    print("YEAR-WISE ANALYTICS".center(60))
    print("="*60)
    print(f"{'Year':<10} {'Orders':<15} {'Total Spend':<20} {'Avg/Order':<15}")
    print("-"*60)
    
    for year in year_spend.keys():
        orders = year_orders.get(year, 0)
        spend = year_spend.get(year, 0)
        avg = spend / orders if orders > 0 else 0
        print(f"{year:<10} {orders:<15} ₹{spend:>17,.2f} ₹{avg:>13,.2f}")
    
    print("="*60)


def show_month_wise(db: OrderDatabase, year: int):
    """Show month-wise analytics for a specific year."""
    analytics = OrderAnalytics(db)
    month_spend = analytics.get_month_wise_spend(year)
    month_orders = analytics.get_month_wise_orders(year)
    
    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    
    print("\n" + "="*60)
    print(f"MONTHLY ANALYTICS - {year}".center(60))
    print("="*60)
    print(f"{'Month':<10} {'Orders':<15} {'Total Spend':<20} {'Avg/Order':<15}")
    print("-"*60)
    
    for month in range(1, 13):
        if month in month_spend:
            orders = month_orders.get(month, 0)
            spend = month_spend.get(month, 0)
            avg = spend / orders if orders > 0 else 0
            month_name = month_names[month]
            print(f"{month_name:<10} {orders:<15} ₹{spend:>17,.2f} ₹{avg:>13,.2f}")
    
    print("="*60)


def show_restaurant_wise(db: OrderDatabase, limit: int = 15):
    """Show restaurant-wise analytics."""
    analytics = OrderAnalytics(db)
    top_restaurants = analytics.get_top_restaurants(limit)
    
    print("\n" + "="*80)
    print(f"TOP {limit} RESTAURANTS".center(80))
    print("="*80)
    print(f"{'Rank':<6} {'Restaurant':<40} {'Orders':<10} {'Total Spend':<20}")
    print("-"*80)
    
    for idx, (name, spend, count) in enumerate(top_restaurants, 1):
        # Truncate long restaurant names
        display_name = name[:37] + "..." if len(name) > 40 else name
        print(f"{idx:<6} {display_name:<40} {count:<10} ₹{spend:>17,.2f}")
    
    print("="*80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Zomato Spend Analysis Tool",
        epilog="Examples:\n"
               "  python main.py ingest zomato_emails.mbox\n"
               "  python main.py stats\n"
               "  python main.py year-wise\n"
               "  python main.py month-wise 2024\n"
               "  python main.py restaurants",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest MBOX file')
    ingest_parser.add_argument('mbox_file', help='Path to MBOX file')
    ingest_parser.add_argument('-v', '--verbose', action='store_true', 
                              help='Verbose output')
    ingest_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                              help='Database path (default: %(default)s)')
    ingest_parser.add_argument('--clear-db', action='store_true',
                              help='Clear/drop database before ingesting')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show overall statistics')
    stats_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                             help='Database path (default: %(default)s)')
    
    # Year-wise command
    year_parser = subparsers.add_parser('year-wise', help='Show year-wise analytics')
    year_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                            help='Database path (default: %(default)s)')
    
    # Month-wise command
    month_parser = subparsers.add_parser('month-wise', help='Show month-wise analytics')
    month_parser.add_argument('year', type=int, help='Year to analyze')
    month_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                             help='Database path (default: %(default)s)')
    
    # Restaurants command
    rest_parser = subparsers.add_parser('restaurants', help='Show restaurant-wise analytics')
    rest_parser.add_argument('-n', '--limit', type=int, default=15,
                            help='Number of restaurants to show (default: %(default)s)')
    rest_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                            help='Database path (default: %(default)s)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to JSON')
    export_parser.add_argument('output_file', help='Output JSON file path')
    export_parser.add_argument('-db', '--database', default=config.DATABASE_PATH,
                              help='Database path (default: %(default)s)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize database
    db = OrderDatabase(args.database)
    
    try:
        if args.command == 'ingest':
            if hasattr(args, 'clear_db') and args.clear_db:
                db.drop_all_tables()
                db = OrderDatabase(args.database)  # Reinitialize with fresh schema
                print("Database cleared.")
            ingest_mbox(args.mbox_file, db, args.verbose)
            show_stats(db)
        
        elif args.command == 'stats':
            show_stats(db)
            show_year_wise(db)
        
        elif args.command == 'year-wise':
            show_year_wise(db)
        
        elif args.command == 'month-wise':
            show_month_wise(db, args.year)
        
        elif args.command == 'restaurants':
            show_restaurant_wise(db, args.limit)
        
        elif args.command == 'export':
            analytics = OrderAnalytics(db)
            orders = db.get_all_orders()
            
            data = {
                'summary': analytics.get_stats_summary(),
                'year_wise_spend': analytics.get_year_wise_spend(),
                'year_wise_orders': analytics.get_year_wise_orders(),
                'top_restaurants': [
                    {
                        'restaurant': name,
                        'total_spend': spend,
                        'order_count': count
                    }
                    for name, spend, count in analytics.get_top_restaurants(100)
                ],
                'orders': [
                    {
                        'order_id': o.order_id,
                        'order_date': o.order_date.isoformat(),
                        'restaurant': o.restaurant_name,
                        'total_amount': o.total_amount,
                        'delivery_fee': o.delivery_fee,
                        'discount': o.discount
                    }
                    for o in orders
                ]
            }
            
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Data exported to {output_path}")
    
    finally:
        db.close()


if __name__ == '__main__':
    main()
