import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("HOST", "127.0.0.1"),
    "port": 3306,
    "database": os.getenv("DB_NAME", "cargo_game"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "autocommit": True,
}

# Game Settings
START_MONEY = 1000
START_RANGE = 2000
WIN_AMOUNT = 10000
FUEL_RATE = 2

TUTORIAL_REWARD = 1200

# Contract Data
BASIC_CARGO = ['Electronics', 'Food Products', 'Clothing', 'Pharmaceuticals', 'Books', 'Furniture', 'Automotive Parts']

RANDOM_TYPES = [
    {'name': 'Hospital Supplies', 'money': 3000, 'is_fraud': False},
    {'name': 'Lab Equipment', 'money': 3500, 'is_fraud': False},
    {'name': 'Industrial Machinery', 'money': 6000, 'is_fraud': True},
    {'name': 'Luxury Goods', 'money': 5000, 'is_fraud': True}
]