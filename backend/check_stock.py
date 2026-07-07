#!/usr/bin/env python3
from app.database.connection import SessionLocal
from app.database.schema import Stock

db = SessionLocal()
count = db.query(Stock).count()
print(f'Stock records from backend: {count}')
latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
if latest_stock:
    print(f'Latest stock date: {latest_stock.date}')
db.close()
