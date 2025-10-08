"""
Global Cargo Empire - Configuration
Software 1 Project - Metropolia UAS
"""

# Database Configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'cargo_game',
    'user': 'root',
    'password': '9594',
    'autocommit': True
}

# Game Settings
START_MONEY = 1000
START_RANGE = 2000
WIN_AMOUNT = 10000
FUEL_RATE = 2  # €1 = 2km

TUTORIAL_REWARD      = 1200
HOSPITAL_REWARD      = 3000
RESEARCH_LAB_REWARD  = 3500
INDUSTRIAL_REWARD    = 6000
INDUSTRIAL_FUEL_BONUS = 300
LUXURY_REWARD        = 5000
LUXURY_FUEL_BONUS     = 200