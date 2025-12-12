**Global Cargo Empire**
A full-stack logistics strategy game where players manage an air freight business using real-world geospatial data.

**Key Features**
Persistent Gameplay: Players can close the browser and resume their exact session later (Database-backed).

Real-World Logic: Distances and fuel costs are calculated using geodesic formulas based on real airport coordinates.

Risk System: A progressive game loop forces players to move from safe contracts to high-risk "Special Operations" involving potential fraud.

Smart Bankruptcy: The server intelligently detects if a player is "soft-locked" (no money + no fuel) and triggers Game Over.

**Tech Stack**
Frontend: JavaScript (ES6), HTML5, CSS3, Leaflet.js (Maps).

Backend: Python (Flask), Geopy.

Database: MariaDB / MySQL.

**Quick Start**
1. python server.py
Open browser at: http://127.0.0.1:5000

**How to Play**
Login: Enter any username. (Existing names resume progress).

Phase 1 (Tutorial): Complete the first flight to learn mechanics.

Phase 2 (Growth): Complete safe "Normal" contracts to build capital.

Phase 3 (Risk): After 2 safe flights, you must choose a Risky Contract (High Reward vs. Fraud).

Win: Reach €10,000. | Lose: Bankruptcy.

Developed by Group 5
