"""
Global Cargo Empire
"""
import random
import mysql.connector
from geopy import distance

# import contracts
from confi import *
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)



def get_airports_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT ident as code, name, latitude_deg as lat, longitude_deg as lon FROM airport WHERE continent = 'EU' AND type = 'large_airport' ORDER BY RAND() LIMIT 30"
    cursor.execute(sql)
    data = cursor.fetchall()
    conn.close()
    return data

def get_airport_by_code(code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT ident as code, name, latitude_deg as lat, longitude_deg as lon FROM airport WHERE ident = %s"
    cursor.execute(sql, (code,))
    data = cursor.fetchone()
    conn.close()
    return data

def calculate_distance(lat1, lon1, lat2, lon2):
    return distance.distance((lat1, lon1), (lat2, lon2)).km

def create_game_in_db(player_name, start_loc):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """INSERT INTO game 
             (player_name, money, player_range, current_location, status, game_phase, normal_flight_count) 
             VALUES (%s, %s, %s, %s, 'active', 1, 0)"""
    cursor.execute(sql, (player_name, START_MONEY, START_RANGE, start_loc))
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return game_id

def get_active_game(player_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM game WHERE player_name = %s AND status = 'active' LIMIT 1"
    cursor.execute(sql, (player_name,))
    game = cursor.fetchone()
    conn.close()
    return game

def update_game_state(game_id, money, fuel, location, phase, normal_count, status='active'):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """UPDATE game 
             SET money=%s, player_range=%s, current_location=%s, game_phase=%s, normal_flight_count=%s, status=%s 
             WHERE id=%s"""
    cursor.execute(sql, (money, fuel, location, phase, normal_count, status, game_id))
    conn.commit()
    conn.close()