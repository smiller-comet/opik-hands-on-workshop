import os
import sqlite3
import json

# --- CONFIGURATION ---
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ohm_sweet_ohm.db")
FAQ_PATH = os.path.join(DATA_DIR, "faq.txt")

# --- 1. RAW DATA (Your JSON Data) ---
# I have pasted your data into these lists directly.

RAW_PRODUCTS = [
  { "product_id": "AUDIO-101", "name": "NexusWave Pro Headphones", "description": "Premium noise-cancelling wireless headphones with 40-hour battery life and crystal-clear audio", "price": 149.99, "category": "Audio", "in_stock": True },
  { "product_id": "AUDIO-102", "name": "SonicBlast Studio Headphones", "description": "Professional studio headphones with deep bass and noise isolation, perfect for music production", "price": 119.99, "category": "Audio", "in_stock": True },
  { "product_id": "AUDIO-103", "name": "AirStream Wireless Earbuds", "description": "Lightweight wireless earbuds with 12-hour battery and quick charge technology", "price": 79.99, "category": "Audio", "in_stock": True },
  { "product_id": "WEAR-201", "name": "PulseSync Fitness Tracker", "description": "Advanced fitness tracking smartwatch with heart rate monitor, GPS, and 7-day battery life", "price": 249.99, "category": "Wearables", "in_stock": True },
  { "product_id": "WEAR-202", "name": "FitZone Activity Band", "description": "Budget-friendly fitness tracker with step counting, sleep tracking, and 10-day battery", "price": 89.99, "category": "Wearables", "in_stock": True },
  { "product_id": "WEAR-203", "name": "ProActive Sports Watch", "description": "Rugged sports watch with GPS, water resistance, and advanced workout tracking", "price": 199.99, "category": "Wearables", "in_stock": True },
  { "product_id": "CASE-301", "name": "ShieldMax Phone Protector", "description": "Military-grade protective case with shock absorption and screen protection", "price": 34.99, "category": "Accessories", "in_stock": True },
  { "product_id": "CASE-302", "name": "ClearGuard Transparent Case", "description": "Slim transparent case that shows off your phone while providing protection", "price": 24.99, "category": "Accessories", "in_stock": True },
  { "product_id": "DESK-401", "name": "ElevateDesk Adjustable Stand", "description": "Ergonomic aluminum laptop stand with adjustable height and ventilation", "price": 79.99, "category": "Office", "in_stock": True },
  { "product_id": "DESK-402", "name": "CompactDesk Mini Stand", "description": "Space-saving laptop stand perfect for small desks and portable setups", "price": 49.99, "category": "Office", "in_stock": True },
  { "product_id": "CABLE-501", "name": "PowerFlow USB-C Charger", "description": "6ft fast-charging USB-C cable with braided design and data transfer support", "price": 19.99, "category": "Accessories", "in_stock": True },
  { "product_id": "AUDIO-601", "name": "SoundSphere Portable Speaker", "description": "Waterproof Bluetooth speaker with 360-degree sound and 15-hour battery", "price": 129.99, "category": "Audio", "in_stock": True },
  { "product_id": "AUDIO-602", "name": "BassBoom Party Speaker", "description": "High-powered portable speaker with deep bass and LED lights for parties", "price": 159.99, "category": "Audio", "in_stock": True },
  { "product_id": "MOUSE-701", "name": "PrecisionPoint Wireless Mouse", "description": "Ergonomic wireless mouse with precision tracking and long battery life", "price": 49.99, "category": "Office", "in_stock": False },
  { "product_id": "MOUSE-702", "name": "SpeedClick Gaming Mouse", "description": "High-DPI gaming mouse with RGB lighting and programmable buttons", "price": 69.99, "category": "Office", "in_stock": True },
  { "product_id": "TABLET-801", "name": "FlexStand Tablet Mount", "description": "Adjustable stand for tablets and e-readers with flexible positioning", "price": 39.99, "category": "Office", "in_stock": True },
  { "product_id": "AUDIO-901", "name": "BassBoost Earbuds", "description": "True wireless earbuds with active noise cancellation and 8-hour battery", "price": 89.99, "category": "Audio", "in_stock": True },
  { "product_id": "CABLE-1001", "name": "MultiCharge Cable Set", "description": "3-in-1 charging cable set with USB-C, Lightning, and Micro-USB connectors", "price": 29.99, "category": "Accessories", "in_stock": True },
  { "product_id": "GAME-1101", "name": "NexGen Pro Gaming Console", "description": "Latest generation gaming console with 4K gaming, ray tracing, and exclusive titles", "price": 499.99, "category": "Gaming", "in_stock": True },
  { "product_id": "GAME-1102", "name": "PlayStation 5", "description": "Sony PlayStation 5 with ultra-fast SSD, 3D audio, and DualSense controller", "price": 499.99, "category": "Gaming", "in_stock": True },
  { "product_id": "GAME-1103", "name": "Xbox Series X", "description": "Microsoft Xbox Series X with 4K gaming, backward compatibility, and Game Pass", "price": 499.99, "category": "Gaming", "in_stock": True },
  { "product_id": "GAME-1104", "name": "Nintendo Switch OLED", "description": "Nintendo Switch with vibrant OLED screen, enhanced audio, and portable gaming", "price": 349.99, "category": "Gaming", "in_stock": True },
  { "product_id": "GAME-1201", "name": "ProGamer Controller", "description": "Professional gaming controller with customizable buttons and haptic feedback", "price": 79.99, "category": "Gaming", "in_stock": True },
  { "product_id": "GAME-1202", "name": "Racing Wheel Pro", "description": "Force feedback racing wheel with pedals for realistic driving simulation", "price": 299.99, "category": "Gaming", "in_stock": True },
  { "product_id": "GAME-1203", "name": "FightStick Arcade Controller", "description": "Arcade-style fight stick with mechanical buttons for fighting games", "price": 149.99, "category": "Gaming", "in_stock": True },
  { "product_id": "TV-1301-55", "name": "CrystalView 4K Smart TV - 55 inch", "description": "55-inch 4K UHD Smart TV with HDR, voice control, and streaming apps", "price": 599.99, "category": "TVs", "in_stock": True, "size": "55 inch" },
  { "product_id": "TV-1301-65", "name": "CrystalView 4K Smart TV - 65 inch", "description": "65-inch 4K UHD Smart TV with HDR, voice control, and streaming apps", "price": 899.99, "category": "TVs", "in_stock": True, "size": "65 inch" },
  { "product_id": "TV-1301-75", "name": "CrystalView 4K Smart TV - 75 inch", "description": "75-inch 4K UHD Smart TV with HDR, voice control, and streaming apps", "price": 1299.99, "category": "TVs", "in_stock": True, "size": "75 inch" },
  { "product_id": "TV-1302-55", "name": "UltraBright OLED TV - 55 inch", "description": "55-inch OLED TV with perfect blacks, Dolby Vision, and premium sound", "price": 1299.99, "category": "TVs", "in_stock": True, "size": "55 inch" },
  { "product_id": "TV-1302-65", "name": "UltraBright OLED TV - 65 inch", "description": "65-inch OLED TV with perfect blacks, Dolby Vision, and premium sound", "price": 1899.99, "category": "TVs", "in_stock": True, "size": "65 inch" },
  { "product_id": "TV-1302-75", "name": "UltraBright OLED TV - 75 inch", "description": "75-inch OLED TV with perfect blacks, Dolby Vision, and premium sound", "price": 2499.99, "category": "TVs", "in_stock": True, "size": "75 inch" },
  { "product_id": "TV-1303-55", "name": "BudgetSmart LED TV - 55 inch", "description": "55-inch LED Smart TV with 4K resolution and built-in streaming", "price": 399.99, "category": "TVs", "in_stock": True, "size": "55 inch" },
  { "product_id": "TV-1303-65", "name": "BudgetSmart LED TV - 65 inch", "description": "65-inch LED Smart TV with 4K resolution and built-in streaming", "price": 599.99, "category": "TVs", "in_stock": True, "size": "65 inch" },
  { "product_id": "TV-1303-75", "name": "BudgetSmart LED TV - 75 inch", "description": "75-inch LED Smart TV with 4K resolution and built-in streaming", "price": 899.99, "category": "TVs", "in_stock": True, "size": "75 inch" }
]

RAW_ORDERS = [
  { "order_id": "TECH-001", "customer_name": "Steve Mobs", "customer_email": "steve.mobs@email.com", "days_since_order": 5, "status": "shipped", "current_location": "Distribution Center - San Francisco, CA", "items": [{"product_id": "AUDIO-101", "quantity": 1, "price": 149.99}] },
  { "order_id": "TECH-002", "customer_name": "Taylor Shift", "customer_email": "taylor.shift@email.com", "days_since_order": 3, "status": "in_transit", "current_location": "In Transit - Oakland, CA", "items": [{"product_id": "WEAR-201", "quantity": 1, "price": 249.99}, {"product_id": "CASE-301", "quantity": 2, "price": 34.99}] },
  { "order_id": "TECH-003", "customer_name": "Albert I. Stein", "customer_email": "albert.stine@email.com", "days_since_order": 1, "status": "processing", "current_location": "Warehouse - Processing", "items": [{"product_id": "DESK-401", "quantity": 1, "price": 79.99}] },
  { "order_id": "TECH-004", "customer_name": "Meryl Streak", "customer_email": "meryl.streak@email.com", "days_since_order": 12, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "CABLE-501", "quantity": 3, "price": 19.99}] },
  { "order_id": "TECH-005", "customer_name": "Elon Tusk", "customer_email": "elon.tusk@email.com", "days_since_order": 0, "status": "pending", "current_location": "Order Received - Awaiting Processing", "items": [{"product_id": "AUDIO-101", "quantity": 2, "price": 149.99}, {"product_id": "AUDIO-601", "quantity": 1, "price": 129.99}] },
  { "order_id": "TECH-006", "customer_name": "Lebron Jams", "customer_email": "Lebron.Jams@email.com", "days_since_order": 4, "status": "shipped", "current_location": "Distribution Center - San Francisco, CA", "items": [{"product_id": "MOUSE-702", "quantity": 1, "price": 69.99}, {"product_id": "DESK-401", "quantity": 1, "price": 79.99}] },
  { "order_id": "TECH-007", "customer_name": "Selena Williams", "customer_email": "selena.williams@email.com", "days_since_order": 2, "status": "in_transit", "current_location": "Out for Delivery - San Francisco, CA", "items": [{"product_id": "WEAR-201", "quantity": 1, "price": 249.99}] },
  { "order_id": "TECH-008", "customer_name": "Serena Gomez", "customer_email": "serena.gomez@email.com", "days_since_order": 8, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "CASE-301", "quantity": 4, "price": 34.99}, {"product_id": "CABLE-501", "quantity": 2, "price": 19.99}] },
  { "order_id": "TECH-009", "customer_name": "Michael Gordon", "customer_email": "michael.gordon@email.com", "days_since_order": 2, "status": "processing", "current_location": "Warehouse - Processing", "items": [{"product_id": "AUDIO-601", "quantity": 1, "price": 129.99}, {"product_id": "TABLET-801", "quantity": 1, "price": 39.99}] },
  { "order_id": "TECH-010", "customer_name": "Brad Litt", "customer_email": "brad.litt@email.com", "days_since_order": 6, "status": "shipped", "current_location": "Distribution Center - San Francisco, CA", "items": [{"product_id": "WEAR-201", "quantity": 1, "price": 249.99}, {"product_id": "CASE-301", "quantity": 1, "price": 34.99}] },
  { "order_id": "TECH-011", "customer_name": "Lyon Woods", "customer_email": "lyon.woods@email.com", "days_since_order": 0, "status": "pending", "current_location": "Order Received - Awaiting Processing", "items": [{"product_id": "AUDIO-101", "quantity": 1, "price": 149.99}] },
  { "order_id": "TECH-012", "customer_name": "Bill Smith", "customer_email": "bill.smith@email.com", "days_since_order": 15, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "DESK-401", "quantity": 2, "price": 79.99}] },
  { "order_id": "TECH-013", "customer_name": "Bill Bates", "customer_email": "bill.bates@email.com", "days_since_order": 1, "status": "processing", "current_location": "Warehouse - Quality Check", "items": [{"product_id": "GAME-1102", "quantity": 1, "price": 499.99}, {"product_id": "GAME-1201", "quantity": 2, "price": 79.99}] },
  { "order_id": "TECH-014", "customer_name": "Wayne the Sock Johnson", "customer_email": "wayne.johnson@email.com", "days_since_order": 4, "status": "in_transit", "current_location": "In Transit - Sacramento, CA", "items": [{"product_id": "TV-1301-65", "quantity": 1, "price": 899.99}] },
  { "order_id": "TECH-015", "customer_name": "Bryan Reynolds", "customer_email": "bryan.reynolds@email.com", "days_since_order": 3, "status": "in_transit", "current_location": "In Transit - San Jose, CA", "items": [{"product_id": "GAME-1104", "quantity": 1, "price": 349.99}, {"product_id": "AUDIO-901", "quantity": 1, "price": 89.99}] },
  { "order_id": "TECH-016", "customer_name": "Travis Swift", "customer_email": "travis.swift@email.com", "days_since_order": 10, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "TV-1302-55", "quantity": 1, "price": 1299.99}] },
  { "order_id": "TECH-017", "customer_name": "Keanu Reevis", "customer_email": "keanu.reevis@email.com", "days_since_order": 0, "status": "pending", "current_location": "Order Received - Awaiting Processing", "items": [{"product_id": "GAME-1101", "quantity": 1, "price": 499.99}, {"product_id": "GAME-1202", "quantity": 1, "price": 299.99}] },
  { "order_id": "TECH-018", "customer_name": "Josh Ballen", "customer_email": "josh.ballen@email.com", "days_since_order": 5, "status": "shipped", "current_location": "Distribution Center - San Francisco, CA", "items": [{"product_id": "AUDIO-102", "quantity": 1, "price": 119.99}, {"product_id": "AUDIO-103", "quantity": 1, "price": 79.99}] },
  { "order_id": "TECH-019", "customer_name": "Tom Brody", "customer_email": "tom.brody@email.com", "days_since_order": 2, "status": "in_transit", "current_location": "In Transit - Fresno, CA", "items": [{"product_id": "TV-1303-75", "quantity": 1, "price": 899.99}, {"product_id": "CABLE-1001", "quantity": 2, "price": 29.99}] },
  { "order_id": "TECH-020", "customer_name": "Mark Grufallo", "customer_email": "mark.grufallo@email.com", "days_since_order": 13, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "WEAR-202", "quantity": 1, "price": 89.99}, {"product_id": "CASE-302", "quantity": 2, "price": 24.99}] },
  { "order_id": "TECH-021", "customer_name": "Michaelangelo DiCaprio", "customer_email": "michaelangelo.dicaprio@email.com", "days_since_order": 1, "status": "processing", "current_location": "Warehouse - Packaging", "items": [{"product_id": "GAME-1103", "quantity": 1, "price": 499.99}, {"product_id": "GAME-1203", "quantity": 1, "price": 149.99}] },
  { "order_id": "TECH-022", "customer_name": "Emma Scone", "customer_email": "emma.scone@email.com", "days_since_order": 3, "status": "shipped", "current_location": "Distribution Center - San Francisco, CA", "items": [{"product_id": "TV-1301-55", "quantity": 1, "price": 599.99}, {"product_id": "AUDIO-602", "quantity": 1, "price": 159.99}] },
  { "order_id": "TECH-023", "customer_name": "Leonel Besti", "customer_email": "leo.besti@email.com", "days_since_order": 11, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "WEAR-203", "quantity": 1, "price": 199.99}, {"product_id": "DESK-402", "quantity": 1, "price": 49.99}] },
  { "order_id": "TECH-024", "customer_name": "Miles Seller", "customer_email": "miles.seller@email.com", "days_since_order": 1, "status": "pending", "current_location": "Order Received - Awaiting Processing", "items": [{"product_id": "TV-1302-75", "quantity": 1, "price": 2499.99}] },
  { "order_id": "TECH-025", "customer_name": "Tom Bruise", "customer_email": "tom.bruise@email.com", "days_since_order": 7, "status": "delivered", "current_location": "Delivered to Customer", "items": [{"product_id": "AUDIO-101", "quantity": 1, "price": 149.99}, {"product_id": "MOUSE-702", "quantity": 1, "price": 69.99}, {"product_id": "CABLE-501", "quantity": 2, "price": 19.99}] }
]

RAW_STORES = [
  { "store_id": "SF-DOWNTOWN", "name": "Ohm Sweet Ohm Downtown", "address": "123 Market Street, San Francisco, CA 94102", "phone": "(415) 555-0101", "inventory": { "AUDIO-101": 18, "AUDIO-102": 12, "AUDIO-103": 25, "WEAR-201": 0, "WEAR-202": 20, "WEAR-203": 8, "CASE-301": 35, "CASE-302": 28, "DESK-401": 15, "DESK-402": 22, "CABLE-501": 60, "AUDIO-601": 14, "AUDIO-602": 6, "MOUSE-701": 0, "MOUSE-702": 15, "TABLET-801": 22, "AUDIO-901": 20, "CABLE-1001": 45, "GAME-1101": 5, "GAME-1102": 8, "GAME-1103": 6, "GAME-1104": 12, "GAME-1201": 18, "GAME-1202": 3, "GAME-1203": 10, "TV-1301-55": 8, "TV-1301-65": 5, "TV-1301-75": 2, "TV-1302-55": 4, "TV-1302-65": 3, "TV-1302-75": 1, "TV-1303-55": 15, "TV-1303-65": 10, "TV-1303-75": 6 } },
  { "store_id": "SF-UNION", "name": "Ohm Sweet Ohm Union Square", "address": "456 Geary Street, San Francisco, CA 94108", "phone": "(415) 555-0202", "inventory": { "AUDIO-101": 25, "AUDIO-102": 8, "AUDIO-103": 30, "WEAR-201": 8, "WEAR-202": 15, "WEAR-203": 0, "CASE-301": 42, "CASE-302": 35, "DESK-401": 0, "DESK-402": 18, "CABLE-501": 55, "AUDIO-601": 18, "AUDIO-602": 4, "MOUSE-701": 12, "MOUSE-702": 20, "TABLET-801": 28, "AUDIO-901": 0, "CABLE-1001": 50, "GAME-1101": 7, "GAME-1102": 10, "GAME-1103": 8, "GAME-1104": 15, "GAME-1201": 22, "GAME-1202": 5, "GAME-1203": 12, "TV-1301-55": 12, "TV-1301-65": 8, "TV-1301-75": 4, "TV-1302-55": 6, "TV-1302-65": 4, "TV-1302-75": 2, "TV-1303-55": 20, "TV-1303-65": 15, "TV-1303-75": 10 } },
  { "store_id": "SF-MISSION", "name": "Ohm Sweet Ohm Mission District", "address": "789 Valencia Street, San Francisco, CA 94110", "phone": "(415) 555-0303", "inventory": { "AUDIO-101": 0, "AUDIO-102": 15, "AUDIO-103": 18, "WEAR-201": 15, "WEAR-202": 25, "WEAR-203": 10, "CASE-301": 28, "CASE-302": 20, "DESK-401": 18, "DESK-402": 12, "CABLE-501": 48, "AUDIO-601": 0, "AUDIO-602": 8, "MOUSE-701": 8, "MOUSE-702": 12, "TABLET-801": 15, "AUDIO-901": 22, "CABLE-1001": 38, "GAME-1101": 4, "GAME-1102": 6, "GAME-1103": 5, "GAME-1104": 10, "GAME-1201": 15, "GAME-1202": 2, "GAME-1203": 8, "TV-1301-55": 6, "TV-1301-65": 4, "TV-1301-75": 1, "TV-1302-55": 3, "TV-1302-65": 2, "TV-1302-75": 0, "TV-1303-55": 12, "TV-1303-65": 8, "TV-1303-75": 5 } },
  { "store_id": "SF-MARINA", "name": "Ohm Sweet Ohm Marina", "address": "321 Chestnut Street, San Francisco, CA 94123", "phone": "(415) 555-0404", "inventory": { "AUDIO-101": 20, "AUDIO-102": 10, "AUDIO-103": 22, "WEAR-201": 10, "WEAR-202": 18, "WEAR-203": 6, "CASE-301": 0, "CASE-302": 30, "DESK-401": 12, "DESK-402": 15, "CABLE-501": 52, "AUDIO-601": 16, "AUDIO-602": 5, "MOUSE-701": 0, "MOUSE-702": 18, "TABLET-801": 20, "AUDIO-901": 18, "CABLE-1001": 0, "GAME-1101": 6, "GAME-1102": 9, "GAME-1103": 7, "GAME-1104": 13, "GAME-1201": 20, "GAME-1202": 4, "GAME-1203": 11, "TV-1301-55": 10, "TV-1301-65": 6, "TV-1301-75": 3, "TV-1302-55": 5, "TV-1302-65": 3, "TV-1302-75": 1, "TV-1303-55": 18, "TV-1303-65": 12, "TV-1303-75": 8 } },
  { "store_id": "SF-SOMA", "name": "Ohm Sweet Ohm SoMa", "address": "555 Folsom Street, San Francisco, CA 94107", "phone": "(415) 555-0505", "inventory": { "AUDIO-101": 15, "AUDIO-102": 6, "AUDIO-103": 20, "WEAR-201": 14, "WEAR-202": 22, "WEAR-203": 8, "CASE-301": 25, "CASE-302": 18, "DESK-401": 20, "DESK-402": 10, "CABLE-501": 0, "AUDIO-601": 12, "AUDIO-602": 3, "MOUSE-701": 15, "MOUSE-702": 16, "TABLET-801": 18, "AUDIO-901": 16, "CABLE-1001": 40, "GAME-1101": 5, "GAME-1102": 7, "GAME-1103": 6, "GAME-1104": 11, "GAME-1201": 17, "GAME-1202": 3, "GAME-1203": 9, "TV-1301-55": 9, "TV-1301-65": 5, "TV-1301-75": 2, "TV-1302-55": 4, "TV-1302-65": 2, "TV-1302-75": 1, "TV-1303-55": 16, "TV-1303-65": 11, "TV-1303-75": 7 } }
]

RAW_PROMOTIONS = [
  { "promotion_id": "PROMO-001", "type": "store_wide", "store_id": "SF-DOWNTOWN", "description": "20% off all Audio products", "discount_percent": 20, "category": "Audio" },
  { "promotion_id": "PROMO-002", "type": "store_wide", "store_id": "SF-UNION", "description": "15% off all Office products", "discount_percent": 15, "category": "Office" },
  { "promotion_id": "PROMO-003", "type": "product_specific", "store_id": "SF-MISSION", "description": "25% off PulseSync Fitness Tracker", "discount_percent": 25, "product_id": "WEAR-201" },
  { "promotion_id": "PROMO-004", "type": "store_wide", "store_id": "SF-MARINA", "description": "10% off all Accessories", "discount_percent": 10, "category": "Accessories" },
  { "promotion_id": "PROMO-005", "type": "product_specific", "store_id": "SF-SOMA", "description": "30% off NexusWave Pro Headphones", "discount_percent": 30, "product_id": "AUDIO-101" },
  { "promotion_id": "PROMO-006", "type": "product_specific", "store_id": "SF-DOWNTOWN", "description": "$20 off ElevateDesk Adjustable Stand", "discount_amount": 20.00, "product_id": "DESK-401" },
  { "promotion_id": "PROMO-007", "type": "store_wide", "store_id": "SF-UNION", "description": "Buy 2 Get 1 Free on all Cables", "discount_type": "bogo", "category": "Accessories", "product_ids": ["CABLE-501", "CABLE-1001"] },
  { "promotion_id": "PROMO-008", "type": "store_wide", "store_id": "SF-DOWNTOWN", "description": "15% off all Gaming products", "discount_percent": 15, "category": "Gaming" },
  { "promotion_id": "PROMO-009", "type": "product_specific", "store_id": "SF-UNION", "description": "$50 off PlayStation 5", "discount_amount": 50.00, "product_id": "GAME-1102" },
  { "promotion_id": "PROMO-010", "type": "product_specific", "store_id": "SF-MISSION", "description": "$50 off Xbox Series X", "discount_amount": 50.00, "product_id": "GAME-1103" },
  { "promotion_id": "PROMO-011", "type": "product_specific", "store_id": "SF-MARINA", "description": "$30 off Nintendo Switch OLED", "discount_amount": 30.00, "product_id": "GAME-1104" },
  { "promotion_id": "PROMO-012", "type": "store_wide", "store_id": "SF-SOMA", "description": "10% off all TVs", "discount_percent": 10, "category": "TVs" },
  { "promotion_id": "PROMO-013", "type": "product_specific", "store_id": "SF-DOWNTOWN", "description": "$100 off CrystalView 4K Smart TV - 65 inch", "discount_amount": 100.00, "product_id": "TV-1301-65" },
  { "promotion_id": "PROMO-014", "type": "product_specific", "store_id": "SF-UNION", "description": "$200 off UltraBright OLED TV - 75 inch", "discount_amount": 200.00, "product_id": "TV-1302-75" },
  { "promotion_id": "PROMO-015", "type": "store_wide", "store_id": "SF-MISSION", "description": "20% off all Wearables", "discount_percent": 20, "category": "Wearables" },
  { "promotion_id": "PROMO-016", "type": "product_specific", "store_id": "SF-MARINA", "description": "25% off SoundSphere Portable Speaker", "discount_percent": 25, "product_id": "AUDIO-601" },
  { "promotion_id": "PROMO-017", "type": "product_specific", "store_id": "SF-SOMA", "description": "$15 off ProGamer Controller", "discount_amount": 15.00, "product_id": "GAME-1201" },
  { "promotion_id": "PROMO-018", "type": "product_specific", "store_id": "SF-DOWNTOWN", "description": "$50 off Racing Wheel Pro", "discount_amount": 50.00, "product_id": "GAME-1202" },
  { "promotion_id": "PROMO-019", "type": "product_specific", "store_id": "SF-UNION", "description": "20% off BudgetSmart LED TV - 55 inch", "discount_percent": 20, "product_id": "TV-1303-55" },
  { "promotion_id": "PROMO-020", "type": "product_specific", "store_id": "SF-MISSION", "description": "$10 off BassBoost Earbuds", "discount_amount": 10.00, "product_id": "AUDIO-901" },
  { "promotion_id": "PROMO-021", "type": "store_wide", "store_id": "SF-MARINA", "description": "12% off all Gaming accessories", "discount_percent": 12, "category": "Gaming", "product_ids": ["GAME-1201", "GAME-1202", "GAME-1203"] },
  { "promotion_id": "PROMO-022", "type": "product_specific", "store_id": "SF-SOMA", "description": "$30 off CrystalView 4K Smart TV - 75 inch", "discount_amount": 30.00, "product_id": "TV-1301-75" }
]

def setup_directories():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✅ Created directory: {DATA_DIR}")

def create_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Clean slate every time
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- TABLE DEFINITIONS ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (product_id TEXT PRIMARY KEY, name TEXT, description TEXT, price REAL, category TEXT, in_stock INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, customer_name TEXT, customer_email TEXT, status TEXT, days_since_order INTEGER, current_location TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (order_id TEXT, product_id TEXT, quantity INTEGER, unit_price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stores (store_id TEXT PRIMARY KEY, name TEXT, address TEXT, phone TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS store_inventory (store_id TEXT, product_id TEXT, stock_level INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS promotions (promotion_id TEXT PRIMARY KEY, description TEXT, discount_percent REAL, discount_amount REAL, category TEXT, product_ids TEXT)''')

    # --- DATA INSERTION ---

    # 1. PRODUCTS
    for p in RAW_PRODUCTS:
        in_stock_val = 1 if p.get('in_stock', True) else 0
        cursor.execute("INSERT INTO products VALUES (?,?,?,?,?,?)", 
                       (p['product_id'], p['name'], p['description'], p['price'], p['category'], in_stock_val))

    # 2. ORDERS & ORDER ITEMS
    for o in RAW_ORDERS:
        cursor.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)", 
                       (o['order_id'], o['customer_name'], o['customer_email'], o['status'], o['days_since_order'], o['current_location']))
        
        # Populate order_items table for better SQL queries later
        if 'items' in o:
            for item in o['items']:
                cursor.execute("INSERT INTO order_items VALUES (?,?,?,?)",
                               (o['order_id'], item['product_id'], item['quantity'], item['price']))

    # 3. STORES & INVENTORY
    for s in RAW_STORES:
        cursor.execute("INSERT INTO stores VALUES (?,?,?,?)", 
                       (s['store_id'], s['name'], s['address'], s['phone']))
        
        # Flatten the inventory dict into rows
        if 'inventory' in s:
            for pid, qty in s['inventory'].items():
                cursor.execute("INSERT INTO store_inventory VALUES (?,?,?)",
                               (s['store_id'], pid, qty))

    # 4. PROMOTIONS
    for pm in RAW_PROMOTIONS:
        # Handle product_ids (could be list, string, or None)
        p_ids = pm.get('product_ids')
        if p_ids is None and 'product_id' in pm:
            p_ids = pm['product_id'] # Use the single ID if list missing
        
        # If it's a list, join it to string for simple SQLite storage
        if isinstance(p_ids, list):
            p_ids = ",".join(p_ids)
            
        cursor.execute("INSERT INTO promotions VALUES (?,?,?,?,?,?)", 
                       (pm['promotion_id'], pm['description'], pm.get('discount_percent'), pm.get('discount_amount'), pm.get('category'), p_ids))

    conn.commit()
    conn.close()
    print(f"✅ Database created at: {DB_PATH}")

def create_faq():
    faq_content = """
    RETURN POLICY

Ohm Sweet Ohm offers a 30-day return policy on all items. Items must be in their original packaging and unused condition. To initiate a return, please contact customer service with your order number. Return shipping is free for defective items. For other returns, customers are responsible for return shipping costs unless the return is due to our error.

SHIPPING INFORMATION

Standard shipping takes 5-7 business days and costs $5.99. Express shipping (2-3 business days) costs $12.99. Overnight shipping is available for $24.99. Free shipping is available on orders over $50. All orders are shipped from our warehouse in San Francisco within 1-2 business days of order confirmation.

PAYMENT METHODS

We accept all major credit cards (Visa, Mastercard, American Express), PayPal, Apple Pay, and Google Pay. Payment is processed securely at checkout. We do not store your payment information.

WARRANTY INFORMATION

All electronics come with a 1-year manufacturer warranty. Extended warranties are available for purchase at checkout. Warranty claims can be processed through our customer service department or by visiting any of our retail locations in San Francisco.

PRODUCT AVAILABILITY

Product availability is updated in real-time on our website. If an item shows as "out of stock" online, you can check with our retail stores for availability. We also offer backorder options for popular items - you'll be notified when your item is back in stock.

STORE LOCATIONS:
We have five retail locations in San Francisco:
- Ohm Sweet Ohm Downtown: 123 Market Street, San Francisco, CA 94102
- Ohm Sweet Ohm Union Square: 456 Geary Street, San Francisco, CA 94108
- Ohm Sweet Ohm Mission District: 789 Valencia Street, San Francisco, CA 94110
- Ohm Sweet Ohm Marina: 321 Chestnut Street, San Francisco, CA 94123
- Ohm Sweet Ohm SoMa: 555 Folsom Street, San Francisco, CA 94107

You can visit any location to browse products, make returns, or get in-person assistance.

STORE HOURS:
All Ohm Sweet Ohm retail locations are open during the following hours:
- Monday through Friday: 10:00 AM - 9:00 PM
- Saturday: 10:00 AM - 8:00 PM
- Sunday: 11:00 AM - 6:00 PM
Holiday hours may vary. Please check our website for specific holiday schedules.

PRICE MATCHING

We offer price matching on identical items from authorized retailers. The item must be in stock at both locations and the price match must be requested at the time of purchase. Online price matches must be requested within 7 days of purchase.

GIFT CARDS

Gift cards are available for purchase in-store or online. They never expire and can be used for any purchase. Gift cards cannot be returned or refunded for cash.

LOYALTY PROGRAM

Join our loyalty program to earn points on every purchase. Points can be redeemed for discounts on future purchases. Sign up is free and available both online and in-store.

CONTACT INFORMATION

For customer service inquiries, you can reach Ohm Sweet Ohm at:
- Phone: 1-800-555-OHM (1-800-555-646)
- Email: support@ohmsweetohm.com
- Live Chat: Available on our website Monday-Friday, 9 AM - 6 PM PST

ORDER MODIFICATIONS AND CANCELLATIONS
Once an order is placed, our warehouse begins processing it immediately to ensure fast shipping. Therefore, orders can only be cancelled or modified within 1 hour of placement. To request a change, please call our customer support line immediately. We cannot modify orders via email or chat due to processing delays.

REFUND TIMING
Once your return is received and inspected at our warehouse (usually within 3 days of delivery), we will process your refund. The refund will be issued to your original payment method. Please allow 5-10 business days for your bank to post the refund to your account.
    """
    
    with open(FAQ_PATH, "w") as f:
        f.write(faq_content.strip())
    print(f"✅ FAQ Knowledge Base created at: {FAQ_PATH}")

if __name__ == "__main__":
    setup_directories()
    create_database()
    create_faq()
    print("🚀 Lab Environment Ready! You can now run the agent.")