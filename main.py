"""
Global Cargo Empire - Simplified & Choice-Based Random
Software 1 Project - Metropolia UAS
Authors: Chamika Bandara, Tharindu Hettigodage, Darshika Walimunige, Shalika Dasanayake
Date: October 2025
"""

import random
from geopy import distance
import mysql.connector
from confi import *  # expects: DB_CONFIG, START_MONEY, START_RANGE, WIN_AMOUNT, FUEL_RATE,
                     # TUTORIAL_REWARD, HOSPITAL_REWARD, RESEARCH_LAB_REWARD,
                     # INDUSTRIAL_REWARD, INDUSTRIAL_FUEL_BONUS,
                     # LUXURY_REWARD, LUXURY_FUEL_BONUS

# ============================================
# DATABASE CONNECTION
# ============================================
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    print("✅ Database connected!")
except mysql.connector.Error as e:
    print(f"❌ Database connection failed: {e}")
    print("Please check confi.py settings")
    raise SystemExit(1)

# ============================================
# DATABASE HELPERS
# ============================================
def get_airports():
    """Get 30 random European large airports"""
    sql = """SELECT iso_country, ident, name, type, latitude_deg, longitude_deg
             FROM airport
             WHERE continent = 'EU'
               AND type = 'large_airport'
             ORDER BY RAND() LIMIT 30"""
    cur = conn.cursor(dictionary=True)
    cur.execute(sql)
    return cur.fetchall()

def create_game(money, p_range, location, player_name):
    """Create new game in database"""
    sql = """INSERT INTO game (money, player_range, current_location, player_name,
                               status, game_phase, forced_random)
             VALUES (%s, %s, %s, %s, 'active', 1, FALSE)"""
    cur = conn.cursor()
    cur.execute(sql, (money, p_range, location, player_name))
    return cur.lastrowid

def get_airport_info(icao):
    sql = """SELECT ident, name, latitude_deg, longitude_deg, iso_country
             FROM airport
             WHERE ident = %s"""
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, (icao,))
    return cur.fetchone()

def calculate_distance(cur_icao, target_icao):
    a = get_airport_info(cur_icao)
    b = get_airport_info(target_icao)
    return distance.distance((a['latitude_deg'], a['longitude_deg']),
                             (b['latitude_deg'], b['longitude_deg'])).km

def airports_in_range(cur_icao, all_airports, p_range):
    out = []
    for ap in all_airports:
        d = calculate_distance(cur_icao, ap['ident'])
        if 0 < d <= p_range:
            ap_copy = dict(ap)
            ap_copy['distance'] = d
            out.append(ap_copy)
    return out

def update_location(icao, p_range, money, g_id, phase, forced):
    sql = """UPDATE game
             SET current_location=%s, player_range=%s, money=%s,
                 game_phase=%s, forced_random=%s
             WHERE id=%s"""
    cur = conn.cursor()
    cur.execute(sql, (icao, p_range, money, phase, int(forced), g_id))

def save_contract(g_id, ctype, cargo, reward, origin, dest):
    sql = """INSERT INTO contract (game_id, contract_type, cargo_type, reward_eur,
                                   origin_airport, dest_airport, status)
             VALUES (%s,%s,%s,%s,%s,%s,'completed')"""
    cur = conn.cursor()
    cur.execute(sql, (g_id, ctype, cargo, reward, origin, dest))

def save_bonus(g_id, b_type, reward, fuel_bonus, destination, is_fraud):
    sql = """INSERT INTO bonus_opportunity
             (game_id, opportunity_type, reward_money, reward_fuel, destination, status)
             VALUES (%s,%s,%s,%s,%s,%s)"""
    status = 'fraud' if is_fraud else 'success'
    cur = conn.cursor()
    cur.execute(sql, (g_id, b_type, reward, fuel_bonus, destination, status))

# ============================================
# CONTRACT & RANDOM OPTIONS
# ============================================
BASIC_CARGO = ['Electronics', 'Food Products', 'Clothing', 'Pharmaceuticals',
               'Books', 'Furniture', 'Automotive Parts', 'Textiles']

def create_tutorial_contract(cur_icao, all_airports, p_range):
    cand = airports_in_range(cur_icao, all_airports, p_range)
    if not cand: return None
    ap = random.choice(cand)
    return dict(
        type='tutorial', cargo='General Cargo',
        destination=ap['ident'], dest_name=ap['name'],
        distance=ap['distance'], reward=TUTORIAL_REWARD
    )

def create_basic_contracts(cur_icao, all_airports, p_range, count=3):
    cand = airports_in_range(cur_icao, all_airports, p_range)
    count = min(count, len(cand))
    if count == 0: return []
    picks = random.sample(cand, count)
    out = []
    for ap in picks:
        reward = round(200 + 0.5 * ap['distance'], 2)
        out.append(dict(
            type='basic', cargo=random.choice(BASIC_CARGO),
            destination=ap['ident'], dest_name=ap['name'],
            distance=ap['distance'], reward=reward
        ))
    return out

# presets (wording has NO "scam" and we don't show "safe/risky" anywhere)
BONUS_PRESETS = {
    'hospital':     dict(kind='reward', name='🏥 Hospital',      desc='Medical supplies delivery',        money=HOSPITAL_REWARD,     fuel=0,                      fraud=False),
    'research_lab': dict(kind='reward', name='🔬 Research Lab',  desc='Scientific equipment delivery',    money=RESEARCH_LAB_REWARD, fuel=0,                      fraud=False),
    'industrial':   dict(kind='fraud',  name='🏭 Industrial',    desc='Heavy machinery delivery',         money=INDUSTRIAL_REWARD,   fuel=INDUSTRIAL_FUEL_BONUS, fraud=True),
    'luxury_goods': dict(kind='fraud',  name='💎 Luxury Goods',  desc='Designer items delivery',          money=LUXURY_REWARD,       fuel=LUXURY_FUEL_BONUS,     fraud=True),
}

def build_bonus_option(btype, ap):
    p = BONUS_PRESETS[btype]
    return dict(
        key=btype, preset=p,
        destination=ap['ident'], dest_name=ap['name'],
        distance=ap['distance'],
        reward=p['money'], fuel_bonus=p['fuel'], is_fraud=p['fraud'],
        name=p['name'], desc=p['desc']
    )

def create_random_choice_pair(cur_icao, all_airports, p_range):
    """Return two options: one reward-type, one fraud-type, randomized order."""
    cand = airports_in_range(cur_icao, all_airports, p_range)
    if not cand: return None

    # choose airports
    if len(cand) >= 2:
        ap1, ap2 = random.sample(cand, 2)
    else:
        ap1 = ap2 = cand[0]

    reward_type = random.choice(['hospital', 'research_lab'])
    fraud_type  = random.choice(['industrial', 'luxury_goods'])

    opt_reward = build_bonus_option(reward_type, ap1)
    opt_fraud  = build_bonus_option(fraud_type, ap2)

    pair = [opt_reward, opt_fraud]
    random.shuffle(pair)  # randomize order so player can’t memorize position
    return pair

# ============================================
# MAIN GAME
# ============================================
print("\n" + "=" * 70)
print("           🌍 GLOBAL CARGO EMPIRE 🌍")
print("=" * 70)
print("\nWelcome to your cargo airline simulation!")
print(f"Goal: Build a €{WIN_AMOUNT:,} empire without going bankrupt")
print(f"Starting capital: €{START_MONEY:,}")
print(f"Starting fuel range: {START_RANGE:,} km")
print("\nGame Mechanics:")
print("  • Phase 1: Tutorial (single contract)")
print("  • Phase 2: Multiple choice (3 contracts)")
print("  • Phase 3+: Basic or Random (Random shows TWO options — one good, one bad)")
print("\n" + "=" * 70 + "\n")

player_name = input("Enter your airline company name: ")

# Initialize
game_over = False
won = False
money = START_MONEY
player_range = START_RANGE
phase = 1
forced_random = False

all_airports = get_airports()
current_airport = all_airports[0]['ident']
game_id = create_game(money, player_range, current_airport, player_name)

start_airport_info = get_airport_info(current_airport)
print(f"\n✅ Game started! Your hub: {start_airport_info['name']}\n")
input("Press Enter to begin your first contract...")

while not game_over:
    ap_now = get_airport_info(current_airport)
    print("\n" + "=" * 70)
    print(f"📍 Location: {ap_now['name']}")
    print(f"💰 Money: €{money:.2f}")
    print(f"⛽ Fuel Range: {player_range:.0f} km")
    print(f"🎮 Phase: {phase}")
    print("=" * 70)

    # Rescue refuel if stranded
    if len(airports_in_range(current_airport, all_airports, player_range)) == 0:
        print("\n🚨 No airports are currently within your fuel range.")
        if money >= 1:
            ask = input(f"Buy fuel to continue? (€1 = {FUEL_RATE} km) (y/N): ").strip().lower()
            if ask == 'y':
                try:
                    amt = float(input("€ amount: ").strip())
                    if 0 < amt <= money:
                        player_range += amt * FUEL_RATE
                        money -= amt
                        print(f"✅ +{amt * FUEL_RATE:.0f} km fuel | €{money:.2f} left")
                    else:
                        print("❌ Invalid amount.")
                except ValueError:
                    print("❌ Invalid input.")
        # re-check after optional refuel
        if len(airports_in_range(current_airport, all_airports, player_range)) == 0:
            game_over = True
            print("\n💔 GAME OVER - BANKRUPTCY (No reachable airports and no effective refuel)")
            break

    input("\nPress Enter to continue...")

    selected_contract = None
    selected_bonus = None
    upcoming_km = 0

    # ---------------- PHASE 1: Tutorial ----------------
    if phase == 1:
        print("\n" + "─" * 70)
        print("🎓 TUTORIAL CONTRACT")
        print("─" * 70)
        print("This is your first delivery. Learn the basics!\n")

        c = create_tutorial_contract(current_airport, all_airports, player_range)
        if not c:
            print("❌ No airports in range! Game Over.")
            game_over = True
            continue

        print(f"Cargo Type: {c['cargo']}")
        print(f"Destination: {c['dest_name']} ({c['destination']})")
        print(f"Distance: {c['distance']:.0f} km")
        print(f"Reward: €{c['reward']:.2f}")
        print("─" * 70)

        input("\n✅ Press Enter to accept this contract...")
        selected_contract = c
        upcoming_km = c['distance']

    # ---------------- PHASE 2: Multiple Choice ----------------
    elif phase == 2:
        print("\n" + "─" * 70)
        print("📋 CHOOSE YOUR CONTRACT")
        print("─" * 70)
        print("Select the contract that looks best to you:\n")

        choices = create_basic_contracts(current_airport, all_airports, player_range, 3)
        if not choices:
            print("❌ No contracts available! Game Over.")
            game_over = True
            continue

        for i, c in enumerate(choices, 1):
            print(f"[{i}] Cargo: {c['cargo']}")
            print(f"    To: {c['dest_name']} ({c['destination']})")
            print(f"    Distance: {c['distance']:.0f} km")
            print(f"    Reward: €{c['reward']:.2f}\n")

        print("─" * 70)
        try:
            pick = int(input(f"Select contract (1-{len(choices)}): ").strip())
            if not (1 <= pick <= len(choices)):
                raise ValueError
        except ValueError:
            print("❌ Invalid choice.")
            continue

        selected_contract = choices[pick - 1]
        upcoming_km = selected_contract['distance']

    # ---------------- PHASE 3+: Basic or Random (two-option random) ----------------
    else:
        print("\n" + "─" * 70)
        print("🎲 CONTRACT SELECTION")
        print("─" * 70)

        if forced_random:
            print("⚠️  FORCED RANDOM: You must pick one of the two options below.\n")
            pair = create_random_choice_pair(current_airport, all_airports, player_range)
            if not pair:
                print("❌ No opportunities available! Game Over.")
                game_over = True
                continue

            # Show both options
            for i, b in enumerate(pair, 1):
                extra = f" + {b['fuel_bonus']}km fuel" if b['fuel_bonus'] > 0 else ""
                print(f"[{i}] {b['name']}: {b['desc']}")
                print(f"    Destination: {b['dest_name']} ({b['destination']})")
                print(f"    Distance: {b['distance']:.0f} km")
                print(f"    Promised: €{b['reward']:.2f}{extra}\n")

            try:
                pick = int(input(f"Choose option (1-2): ").strip())
                if pick not in (1, 2): raise ValueError
            except ValueError:
                print("❌ Invalid choice.")
                continue

            selected_bonus = pair[pick - 1]
            upcoming_km = selected_bonus['distance']
            forced_random = False

        else:
            choice = input("\nChoose [1] Basic or [2] Random: ").strip()
            if choice == '1':
                # Basic contract
                choices = create_basic_contracts(current_airport, all_airports, player_range, 1)
                if not choices:
                    print("❌ No contracts available! Game Over.")
                    game_over = True
                    continue
                selected_contract = choices[0]
                forced_random = True  # next time must pick random

                print(f"\n✅ Basic Contract Selected")
                print(f"   Cargo: {selected_contract['cargo']}")
                print(f"   To: {selected_contract['dest_name']} ({selected_contract['destination']})")
                print(f"   Distance: {selected_contract['distance']:.0f} km")
                print(f"   Reward: €{selected_contract['reward']:.2f}")
                print("\n⚠️  Next airport: You MUST take a random contract.")
                upcoming_km = selected_contract['distance']

            elif choice == '2':
                # Random: present two options (one reward, one fraud)
                pair = create_random_choice_pair(current_airport, all_airports, player_range)
                if not pair:
                    print("❌ No opportunities available! Game Over.")
                    game_over = True
                    continue

                print()
                for i, b in enumerate(pair, 1):
                    extra = f" + {b['fuel_bonus']}km fuel" if b['fuel_bonus'] > 0 else ""
                    print(f"[{i}] {b['name']}: {b['desc']}")
                    print(f"    Destination: {b['dest_name']} ({b['destination']})")
                    print(f"    Distance: {b['distance']:.0f} km")
                    print(f"    Promised: €{b['reward']:.2f}{extra}\n")

                try:
                    pick = int(input(f"Choose option (1-2): ").strip())
                    if pick not in (1, 2): raise ValueError
                except ValueError:
                    print("❌ Invalid choice.")
                    continue

                selected_bonus = pair[pick - 1]
                upcoming_km = selected_bonus['distance']
                forced_random = False
            else:
                print("❌ Invalid choice.")
                continue

    input("\nPress Enter to continue...")

    # ---------------- FUEL SHOP ----------------
    print("\n" + "─" * 70)
    print("⛽ FUEL SHOP")
    print("─" * 70)
    print(f"Current fuel: {player_range:.0f} km")
    print(f"Available money: €{money:.2f}")
    print(f"Rate: €1 = {FUEL_RATE} km")
    if upcoming_km:
        print(f"Needed for next leg: {upcoming_km:.0f} km")
    print("─" * 70)

    buy = input("\nBuy fuel? (Y/N): ").strip().upper()
    if buy == 'Y':
        try:
            amount = float(input("€ Amount to spend: ").strip())
            if 0 < amount <= money:
                added = amount * FUEL_RATE
                money -= amount
                player_range += added
                print(f"✅ Purchased {added:.0f} km of fuel")
                print(f"   New balance: €{money:.2f} | Fuel: {player_range:.0f} km")
            elif amount > money:
                print("❌ Not enough money!")
            else:
                print("❌ Invalid amount!")
        except ValueError:
            print("❌ Invalid input!")

    input("\nPress Enter to travel...")

    # ---------------- TRAVEL & RESOLUTION ----------------
    if selected_contract:
        dest = selected_contract['destination']
        dist = selected_contract['distance']
        reward = selected_contract['reward']

        print(f"\n✈️  Traveling {dist:.0f} km to {selected_contract['dest_name']}...")
        player_range -= dist
        current_airport = dest

        print(f"\n✅ CONTRACT COMPLETED!")
        print(f"💰 Payment received: €{reward:.2f}")
        money += reward

        save_contract(game_id, selected_contract['type'], selected_contract['cargo'],
                      reward, ap_now['ident'], dest)

    else:
        dest = selected_bonus['destination']
        dist = selected_bonus['distance']

        print(f"\n✈️  Traveling {dist:.0f} km to {selected_bonus['dest_name']}...")
        player_range -= dist
        current_airport = dest

        print(f"\n📦 Arrived at destination...")
        if selected_bonus['is_fraud']:
            print(f"\n💥 RESULT: No payment received.")
            save_bonus(game_id, selected_bonus['key'], 0, 0, dest, True)
        else:
            print(f"\n✅ BONUS OPPORTUNITY COMPLETED!")
            print(f"💰 Payment received: €{selected_bonus['reward']:.2f}")
            money += selected_bonus['reward']
            if selected_bonus['fuel_bonus'] > 0:
                player_range += selected_bonus['fuel_bonus']
                print(f"⛽ Fuel bonus: +{selected_bonus['fuel_bonus']} km")
            save_bonus(game_id, selected_bonus['key'],
                       selected_bonus['reward'], selected_bonus['fuel_bonus'],
                       dest, False)

    # Update game state
    phase += 1
    update_location(current_airport, player_range, money, game_id, phase, forced_random)

    input("\nPress Enter to continue...")

    # ---------------- WIN/LOSE ----------------
    if money >= WIN_AMOUNT:
        won = True
        game_over = True
        print("\n" + "=" * 70)
        print("🎉🎉🎉 CONGRATULATIONS! YOU WON! 🎉🎉🎉")
        print("=" * 70)
        print(f"🏆 You built a €{money:.2f} cargo empire!")
        print(f"✈️  Phases completed: {phase}")
        print(f"⛽ Fuel remaining: {player_range:.0f} km")
        print("=" * 70)

    elif player_range < 0:
        game_over = True
        print("\n" + "=" * 70)
        print("💔 GAME OVER - BANKRUPTCY 💔")
        print("=" * 70)
        print("❌ You ran out of fuel (negative range).")
        print(f"💰 Final balance: €{money:.2f}")
        print(f"⛽ Final fuel: {player_range:.0f} km")
        print(f"📊 Phases completed: {phase}")
        print("=" * 70)

# ============================================
# GAME END
# ============================================
cur = conn.cursor()
cur.execute("UPDATE game SET status=%s WHERE id=%s", ('won' if won else 'lost', game_id))

print("\n" + "=" * 70)
print("📊 GAME SUMMARY")
print("=" * 70)
print(f"Airline: {player_name}")
print(f"Final Money: €{money:.2f}")
print(f"Final Fuel: {player_range:.0f} km")
print(f"Phases Completed: {phase}")
print(f"Result: {'🏆 VICTORY' if won else '💀 DEFEAT'}")
print("=" * 70)

print("\n✈️  Thanks for playing Global Cargo Empire!")
print("Play again to learn which contracts are trustworthy! 🎮\n")

conn.close()

