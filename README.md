🌍 Global Freight Empire

Global Freight Empire is a logistics simulation game where players build and manage a global cargo airline empire. The game emphasizes strategic decision-making, progressive contracts, and hidden information mechanics, offering both challenge and educational value through realistic scenarios of global freight operations.

🎯 Project Objective

The main objective of this project is to design and develop a simulation game in which the player controls a global freight airline using a progressive contract system and hidden information algorithms.
Through experience and learning, players gain strategic insight while balancing risk, reward, and resource management.

🧭 Vision
2.1 Game Concept

Global Freight Empire is an integrated logistics simulation where players grow an economically viable air cargo business. Players must plan routes, manage resources, and make tactical decisions while navigating hidden risks and rewards that shape their success.

2.2 Core Narrative

You play as an ambitious entrepreneur striving to build the world’s most profitable freight airline.
Starting with a single plane and limited capital at a European hub airport, you’ll begin with simple contracts that gradually evolve into complex decisions involving hidden risks.

Your ultimate goal: Earn €10,000 without going bankrupt — mastering the art of logistics and decision-making along the way.

2.3 Mechanical Overview

Progressive Contract System – Start simple, advance into multi-option and hidden-information contracts.

Resource Management – Balance fuel and finances under pressure.

Strategic Planning – Choose between safe, predictable contracts and risky, high-reward ones.

Hidden Information Learning – Discover through experience which contracts are reliable or fraudulent.

Geographic Realism – All airports and distances reflect real-world data.

Progressive Challenge – Difficulty scales with experience, without revealing system logic.

🕹️ Game Flow
3. Functional Requirements
3.1 Game Initialization

Start at a random European hub airport with €1000 and 2000 km of fuel range.

View current cash, fuel, and location clearly at the start.

3.2 Contract Management

Tutorial Phase (First Airport)

Accept a single tutorial contract to learn core mechanics.

Multiple Choice Phase (Second Airport)

Choose between multiple contracts with different payoffs and distances, learning to compare and strategize.

Basic or Random Phase (Third Airport Onwards)

Choose between a basic or random contract.

Selecting a basic contract forces a random one next time to ensure players face uncertainty.

Voluntarily choosing random contracts gives players control over when they face bonus risks.

3.3 Random Contract System

Hospital Contract → €1000 guaranteed.

Industrial Contract → €5000 + 100km fuel, but always fraudulent.

Players learn trust patterns only through repeated experience.

3.4 Navigation and Movement

View all airports within fuel range and select destinations.

Preview distance and fuel cost before traveling.

Purchase fuel at a rate of €1 per 2km.

3.5 End Conditions

Win Condition → Reach €10,000.

Lose Condition → Unable to afford travel (bankruptcy).

After each game, restart to refine strategy and apply learned knowledge.

3.6 Interface & Feedback

Responsive keyboard shortcuts for smooth gameplay.

Instant visual feedback for every player action.

⚙️ Quality Requirements
4.1 Performance

Airport data queries ≤ 1 second.

Distance calculations ≤ 0.5 seconds.

Contract offers and bonus displays occur instantly.

4.2 Usability

Player actions provide feedback within 0.2 seconds.

Tutorial → Choice → Hidden Information system must feel intuitive.

Bonus contracts describe rewards clearly, without exposing hidden logic.

4.3 Reliability

Game handles invalid inputs gracefully without crashes.

Hidden information system maintains consistent behavioral patterns (hospital = success, industrial = fraud).

Forced random system prevents indefinite safe play to preserve challenge.

4.4 Educational & Engagement

Promotes strategic thinking and risk assessment.

Encourages pattern recognition through trial and learning.

Suitable for ages 12+, introducing real-world geography and decision-making under uncertainty.

🧠 Learning Outcomes

Understand risk vs reward in decision systems.

Apply strategic reasoning to optimize resource management.

Develop geographic awareness through realistic aviation data.

Experience progressive complexity without direct tutorials.

🛠️ Technologies (Suggested Stack)

Frontend: Python (Tkinter / Pygame) or Unity

Backend / Logic: Python / SQL (for airport data and contract logic)

Database: MariaDB / MySQL

Data Source: Real-world airport coordinates dataset (e.g., OpenFlights)

🚀 Future Enhancements

Dynamic weather & risk factors.

AI-driven competitor airlines.

Visual route mapping and analytics.

Cloud-save integration and performance analytics dashboard.
