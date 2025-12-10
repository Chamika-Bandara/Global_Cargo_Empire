from flask import Flask, send_from_directory, jsonify, request
import random
from dotenv import load_dotenv
from confi import *
import main

load_dotenv()
app = Flask(__name__, static_folder="web", static_url_path="")


@app.route("/")
def root():
    return send_from_directory("web", "index.html")


@app.route("/api/config")
def get_game_config():
    return jsonify(
        {"START_MONEY": START_MONEY, "START_RANGE": START_RANGE, "WIN_AMOUNT": WIN_AMOUNT, "FUEL_RATE": FUEL_RATE})


@app.route("/api/login", methods=["POST"])
def login_user():
    data = request.get_json()
    name = data.get("playerName", "UNKNOWN").upper()
    existing_game = main.get_active_game(name)

    if existing_game:
        loc_data = main.get_airport_by_code(existing_game['current_location'])
        return jsonify({
            "status": "resumed",
            "game_id": existing_game['id'],
            "money": float(existing_game['money']),
            "fuel": existing_game['player_range'],
            "location": loc_data,
            "phase": existing_game['game_phase'],
            "normal_flight_count": existing_game['normal_flight_count']
        })
    else:
        all_airports = main.get_airports_from_db()
        start_loc = random.choice(all_airports)
        new_id = main.create_game_in_db(name, start_loc['code'])
        return jsonify({
            "status": "new",
            "game_id": new_id,
            "money": START_MONEY,
            "fuel": START_RANGE,
            "location": start_loc,
            "phase": 1,
            "normal_flight_count": 0
        })


@app.route("/api/contracts", methods=["GET"])
def get_contracts():
    game_id = request.args.get('game_id')
    # select tutorial, normal random
    request_type = request.args.get('type')

    conn = main.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT current_location FROM game WHERE id=%s", (game_id,))
    game = cursor.fetchone()
    conn.close()

    current_ap = main.get_airport_by_code(game['current_location'])
    all_airports = main.get_airports_from_db()
    destinations = [ap for ap in all_airports if ap['code'] != current_ap['code']]
    random.shuffle(destinations)

    options = []

    # tutorial
    if request_type == 'tutorial':
        dest = destinations[0]
        dist = main.calculate_distance(current_ap['lat'], current_ap['lon'], dest['lat'], dest['lon'])
        options.append({
            "type": "tutorial", "cargo": "General Cargo", "destination": dest,
            "distance": round(dist), "cost": round(dist), "reward": TUTORIAL_REWARD, "is_fraud": False
        })

    # normal contract
    elif request_type == 'normal':
        for i in range(3):
            dest = destinations[i]
            dist = main.calculate_distance(current_ap['lat'], current_ap['lon'], dest['lat'], dest['lon'])
            cargo = random.choice(main.BASIC_CARGO)
            reward = round(200 + (0.5 * dist))
            options.append({
                "type": "normal", "cargo": cargo, "destination": dest,
                "distance": round(dist), "cost": round(dist), "reward": reward, "is_fraud": False
            })

    # random contract
    elif request_type == 'random':
        # reward
        dest1 = destinations[0]
        dist1 = main.calculate_distance(current_ap['lat'], current_ap['lon'], dest1['lat'], dest1['lon'])
        good_types = [t for t in main.RANDOM_TYPES if not t['is_fraud']]
        good = random.choice(good_types)
        options.append({
            "type": "special", "cargo": good['name'], "destination": dest1,
            "distance": round(dist1), "cost": round(dist1), "reward": good['money'], "is_fraud": False
        })

        # fraud
        dest2 = destinations[1]
        dist2 = main.calculate_distance(current_ap['lat'], current_ap['lon'], dest2['lat'], dest2['lon'])
        bad_types = [t for t in main.RANDOM_TYPES if t['is_fraud']]
        bad = random.choice(bad_types)
        options.append({
            "type": "special", "cargo": bad['name'], "destination": dest2,
            "distance": round(dist2), "cost": round(dist2), "reward": bad['money'], "is_fraud": True
        })

        random.shuffle(options)

    return jsonify(options)


@app.route("/api/fly", methods=["POST"])
def fly():
    data = request.get_json()
    game_id = data.get('game_id')
    contract = data.get('contract')

    conn = main.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM game WHERE id=%s", (game_id,))
    game = cursor.fetchone()
    conn.close()


    if game['player_range'] < contract['cost']:
        return jsonify({"success": False, "message": "Not enough fuel!"})

    new_fuel = game['player_range'] - contract['cost']
    new_money = float(game['money'])
    message = ""

    if contract['is_fraud']:
        message = "FRAUD! The company vanished."
    else:
        new_money += contract['reward']
        message = "Delivery Successful!"

    # logic for phases and counters
    new_phase = game['game_phase'] + 1
    current_normal_count = game['normal_flight_count']
    new_normal_count = current_normal_count

    if contract['type'] == 'normal':
        new_normal_count += 1
    elif contract['type'] == 'special':
        # reset the counter if pick random
        new_normal_count = 0
    elif contract['type'] == 'tutorial':
        new_normal_count = 0

    # Win or Loss
    status = 'active'
    if new_money >= WIN_AMOUNT:
        status = 'won'
        message = "VICTORY! Empire Built."
    elif new_money <= 0 and new_fuel < 100:
        status = 'lost'
        message = "BANKRUPT! Game Over."

    # Update Data base
    main.update_game_state(
        game_id, new_money, new_fuel,
        contract['destination']['code'],
        new_phase, new_normal_count, status
    )

    return jsonify({
        "success": True,
        "money": new_money,
        "fuel": new_fuel,
        "destination": contract['destination'],
        "message": message,
        "phase": new_phase,
        "normal_flight_count": new_normal_count
    })


@app.route("/api/buy-fuel", methods=["POST"])
def buy_fuel():
    data = request.get_json()
    game_id = data.get('game_id')
    amount = float(data.get('amount'))

    conn = main.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM game WHERE id=%s", (game_id,))
    game = cursor.fetchone()
    conn.close()

    if game['money'] < amount:
        return jsonify({"success": False})

    new_money = float(game['money']) - amount
    new_fuel = game['player_range'] + (amount * FUEL_RATE)

    # Update without changing
    main.update_game_state(
        game_id, new_money, new_fuel,
        game['current_location'], game['game_phase'], game['normal_flight_count']
    )

    return jsonify({"success": True, "money": new_money, "fuel": new_fuel})


if __name__ == "__main__":
    app.run(debug=True, port=5000)