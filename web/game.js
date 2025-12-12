let CONFIG = {};
let gameState = {
    playerName: "",
    money: 0,
    fuel: 0,
    currentLocation: null,
    id: 0,
    gameStarted: false,
    phase: 1,
    normalFlightCount: 0
};
let map, playerMarker, flightLine, hoverLine;

document.addEventListener('DOMContentLoaded', () => {
    fetch("/api/config")
        .then(res => res.json())
        .then(cfg => {
            CONFIG = cfg;
            initMap();
            setupEventListeners();
        });
});

function initMap() {
    map = L.map('map', { zoomControl: false, attributionControl: false }).setView([50.0, 10.0], 4);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);
}

function startGame() {
    const nameInput = document.getElementById('player-name-input');
    if (!nameInput.value) { alert("ENTER NAME"); return; }

    fetch("/api/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ playerName: nameInput.value })
    })
    .then(res => res.json())
    .then(data => {
        gameState.id = data.game_id;
        gameState.money = data.money;
        gameState.fuel = data.fuel;
        gameState.currentLocation = data.location;
        gameState.phase = data.phase;
        gameState.normalFlightCount = data.normal_flight_count;
        gameState.gameStarted = true;

        document.getElementById('intro-layer').classList.add('hidden');
        document.getElementById('game-layer').classList.remove('hidden');
        setTimeout(() => map.invalidateSize(), 100);

        showSubScreen('sub-standby');
        dropPlayerMarker(true);
        updateHUD();
    });
}

window.handleMapClick = function() {
    if(playerMarker) playerMarker.closePopup();

    if (gameState.phase === 1) {
        fetchContracts('tutorial');
    }
    else if (gameState.phase === 2) {
        fetchContracts('normal');
    }
    else {
        setupModeSelect();
    }
}

function setupModeSelect() {
    showSubScreen('sub-mode');
    const btnNormal = document.getElementById('btn-mode-normal');
    const msg = document.getElementById('mode-lock-msg');

    if(gameState.normalFlightCount >= 2) {
        btnNormal.classList.add('locked');
        btnNormal.onclick = null;
        msg.textContent = "SAFE CONTRACT LIMIT REACHED. YOU MUST TAKE A RISK.";
    } else {
        btnNormal.classList.remove('locked');
        btnNormal.onclick = () => fetchContracts('normal');
        msg.textContent = "";
    }
}

function fetchContracts(type) {
    fetch(`/api/contracts?game_id=${gameState.id}&type=${type}`)
        .then(res => res.json())
        .then(contracts => {
            if(type === 'tutorial') {
                setupBriefing(contracts[0]);
            } else {
                displayContractList(contracts, type);
            }
        });
}

function displayContractList(contracts, type) {
    const list = type === 'normal' ? document.getElementById('contracts-list') : document.getElementById('random-list');
    list.innerHTML = '';

    contracts.forEach(c => {
        let card = document.createElement('div');
        card.className = 'contract-card';
        let tagColor = c.type === 'special' ? '#ff6f00' : '#333';
        let tagText = c.type === 'special' ? 'SPECIAL OPPORTUNITY' : 'NORMAL CONTRACT';

        card.innerHTML = `
            <div class="tag" style="background:${tagColor}">${tagText}</div>
            <p class="contract-text">
                Deliver <b>${c.cargo}</b> to <b>${c.destination.name}</b>. <br>
                Fuel: <b>${c.cost}</b> km. <br>
                Reward: <b class="text-green">€${c.reward}</b>.
            </p>
        `;

        // HOVER EVENTS
        card.onmouseenter = () => drawHoverLine(c.destination);
        card.onmouseleave = () => removeHoverLine();

        card.onclick = () => {
            removeHoverLine();
            setupBriefing(c);
        };
        list.appendChild(card);
    });

    if(type === 'normal') showSubScreen('sub-selection');
    else showSubScreen('sub-random');
}

// hover line
function drawHoverLine(dest) {
    if (hoverLine) map.removeLayer(hoverLine);


    hoverLine = L.polyline(
        [[gameState.currentLocation.lat, gameState.currentLocation.lon], [dest.lat, dest.lon]],
        {
            color: '#ff6f00',
            weight: 5,
            dashArray: '10, 15',
            className: 'flight-path-hover',
            opacity: 0.8
        }
    ).addTo(map);

    // path fit to the window
    map.fitBounds(hoverLine.getBounds(), {padding:[50,50]});
}

function removeHoverLine() {
    if (hoverLine) {
        map.removeLayer(hoverLine);
        hoverLine = null;
    }
}

function executeFlight() {
    const c = gameState.selectedContract;


    if(gameState.fuel < c.cost) {
        if(gameState.money >= 10) {
            alert("INSUFFICIENT FUEL");
            triggerBuyFuel();
            return;
        }
    }

    document.getElementById('sub-briefing').classList.remove('active');

    if(flightLine) map.removeLayer(flightLine);
    if(playerMarker) map.removeLayer(playerMarker);


    fetch("/api/fly", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id: gameState.id, contract: c })
    })
    .then(res => res.json())
    .then(result => {

        // check for bankrupt.
        if(result.message.includes("BANKRUPT")) {
            gameState.money = result.money;
            gameState.fuel = result.fuel;
            updateHUD();
            showSubScreen('sub-lose');
            return;
        }

        // error check
        if(!result.success) {
            alert(result.message);
            return;
        }

        // plane moves
        animatePlane(gameState.currentLocation, c.destination, 2000);

        // update data base
        setTimeout(() => {
            gameState.money = result.money;
            gameState.fuel = result.fuel;
            gameState.currentLocation = result.destination;
            gameState.phase = result.phase;
            gameState.normalFlightCount = result.normal_flight_count;

            dropPlayerMarker(false);

            if(result.message.includes("VICTORY")) showSubScreen('sub-win');
            else {
                showResult(!result.message.includes("FRAUD"), c.reward, result.message);
            }
            updateHUD();
        }, 2100);
    });
}

// calculate angle
function calculateBearing(lat1, lon1, lat2, lon2) {
    // Simple angle calculation
    const y = lat2 - lat1;
    const x = lon2 - lon1;
    // Calculate angle in degrees
    const angle = Math.atan2(x, y) * 180 / Math.PI;
    return angle;
}

// animate plane
function animatePlane(start, end, duration) {
    const startLat = start.lat;
    const startLon = start.lon;
    const changeLat = end.lat - startLat;
    const changeLon = end.lon - startLon;
    const startTime = performance.now();

    // Calculate rotation
    const rotation = calculateBearing(startLat, startLon, end.lat, end.lon);

    // Create Icon with rotation
    const planeIcon = L.divIcon({
        className: 'plane-icon-wrapper',

        html: `<div style="transform: rotate(${rotation}deg);" class="plane-icon">✈️</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    const planeMarker = L.marker([startLat, startLon], {icon: planeIcon, zIndexOffset: 1000}).addTo(map);

    const bounds = L.latLngBounds([startLat, startLon], [end.lat, end.lon]);
    map.fitBounds(bounds, {padding: [100, 100], animate: true, duration: 1});

    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const currentLat = startLat + (changeLat * progress);
        const currentLon = startLon + (changeLon * progress);

        planeMarker.setLatLng([currentLat, currentLon]);

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            map.removeLayer(planeMarker);
        }
    }
    requestAnimationFrame(animate);
}

function setupBriefing(c) {
    gameState.selectedContract = c;
    document.getElementById('brief-type').textContent = c.cargo;
    document.getElementById('brief-dest').textContent = c.destination.name;
    document.getElementById('brief-dist').textContent = c.cost;
    document.getElementById('brief-reward').textContent = "€" + c.reward;

    if(flightLine) map.removeLayer(flightLine);
    flightLine = L.polyline(
        [[gameState.currentLocation.lat, gameState.currentLocation.lon], [c.destination.lat, c.destination.lon]],
        {color: '#ff6f00', weight: 3, dashArray: '10, 10'}
    ).addTo(map);
    map.fitBounds(flightLine.getBounds(), {padding:[50,50]});
    showSubScreen('sub-briefing');
}

function updateHUD() {
    document.getElementById('hud-money').textContent = "€" + gameState.money;
    document.getElementById('hud-fuel').textContent = gameState.fuel + " KM";
}

function buyFuelConfirm() {
    const val = parseInt(document.getElementById('fuel-amount').value) || 0;
    if(val <= 0) return;
    fetch("/api/buy-fuel", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id: gameState.id, amount: val })
    }).then(res => res.json()).then(data => {
        if(data.success) { gameState.money = data.money; gameState.fuel = data.fuel; updateHUD(); showSubScreen(gameState.previousSubScreen); }
        else alert("Not enough money!");
    });
}

function dropPlayerMarker(interactive) {
    if(playerMarker) map.removeLayer(playerMarker);
    const icon = L.divIcon({ className: 'player-pin', html: `<div style="background:#ff6f00;width:20px;height:20px;border-radius:50%;border:4px solid white;box-shadow:0 0 10px #000;"></div>`, iconSize: [20,20] });
    playerMarker = L.marker([gameState.currentLocation.lat, gameState.currentLocation.lon], {icon: icon}).addTo(map);
    map.flyTo([gameState.currentLocation.lat, gameState.currentLocation.lon], 5);
    if(interactive) playerMarker.bindPopup(`<div style="text-align:center;"><b style="font-size:24px;">LOCATION</b><br><div style="font-size:20px;margin:5px 0;">${gameState.currentLocation.name}</div><button onclick="handleMapClick()" class="popup-btn">CONTINUE</button></div>`).openPopup();
}
function showResult(success, amount, msgText) {
    showSubScreen('sub-result');
    const title = document.getElementById('res-title');
    const msg = document.getElementById('res-msg');
    const amt = document.getElementById('res-amt');
    if(success) { title.textContent = "SUCCESS"; title.className = "text-green"; msg.textContent = msgText; amt.textContent = "+€" + amount; }
    else { title.textContent = "FAILURE"; title.className = "text-red"; msg.textContent = msgText; amt.textContent = "€0"; }
}
function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }
function showSubScreen(id) { document.querySelectorAll('.sub-screen').forEach(el => el.classList.remove('active')); document.getElementById(id).classList.add('active'); }
function triggerBuyFuel() { const current = document.querySelector('.sub-screen.active').id; if(current !== 'sub-fuel' && current !== 'sub-exit') gameState.previousSubScreen = current; document.getElementById('fuel-amount').value = ''; document.getElementById('fuel-preview').textContent = "FUEL: 0 KM"; showSubScreen('sub-fuel'); }
function triggerExit() { const current = document.querySelector('.sub-screen.active').id; if(current !== 'sub-exit' && current !== 'sub-fuel') gameState.previousSubScreen = current; showSubScreen('sub-exit'); }

function setupEventListeners() {
    document.getElementById('btn-play').addEventListener('click', startGame);
    document.querySelector('.trigger-exit').addEventListener('click', triggerExit);
    document.querySelector('.trigger-buy-fuel').addEventListener('click', triggerBuyFuel);
    document.getElementById('btn-confirm-exit').addEventListener('click', () => location.reload());
    document.getElementById('btn-cancel-exit').addEventListener('click', () => showSubScreen(gameState.previousSubScreen));
    document.getElementById('fuel-amount').addEventListener('input', (e) => { document.getElementById('fuel-preview').textContent = `FUEL: ${(parseInt(e.target.value)||0) * CONFIG.FUEL_RATE} KM`; });
    document.getElementById('btn-buy-confirm').addEventListener('click', buyFuelConfirm);
    document.getElementById('btn-buy-cancel').addEventListener('click', () => showSubScreen(gameState.previousSubScreen));
    document.getElementById('btn-tutorial-confirm').addEventListener('click', executeFlight);
    document.getElementById('btn-mode-random').addEventListener('click', () => fetchContracts('random'));
    document.getElementById('btn-fly').addEventListener('click', executeFlight);
    document.getElementById('btn-cancel-brief').addEventListener('click', () => showSubScreen(gameState.selectedContract.type === 'normal' ? 'sub-selection' : 'sub-random'));
    document.getElementById('btn-back-map').addEventListener('click', () => { showSubScreen('sub-standby'); dropPlayerMarker(true); });
    document.querySelectorAll('.trigger-reset').forEach(btn => btn.addEventListener('click', () => location.reload()));
}