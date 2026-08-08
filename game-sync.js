// Pokémon Nexus Backend Persistence & Synchronization Client
const SYNC_API_BASE_URL = "http://127.0.0.1:5000/api";

// Helper to make API requests with JWT Auth
async function syncApiRequest(endpoint, method = "GET", body = null) {
    const token = localStorage.getItem("pokemonNexusAccess") || localStorage.getItem("pokemonNexusToken");
    const headers = {
        "Content-Type": "application/json"
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const options = {
        method: method,
        headers: headers
    };
    if (body && (method === "POST" || method === "PUT" || method === "PATCH")) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(SYNC_API_BASE_URL + endpoint, options);
        if (response.status === 204) {
            return true;
        }
        if (response.status === 401) {
            console.warn("Unauthorized/Token Expired. Redirecting to login...");
            const refresh = localStorage.getItem("pokemonNexusRefresh");
            if (refresh) {
                const refreshRes = await fetch(SYNC_API_BASE_URL + "/token/refresh/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ refresh })
                });
                if (refreshRes.ok) {
                    const refreshData = await refreshRes.json();
                    localStorage.setItem("pokemonNexusAccess", refreshData.access);
                    localStorage.setItem("pokemonNexusToken", refreshData.access);
                    headers["Authorization"] = `Bearer ${refreshData.access}`;
                    const retryResponse = await fetch(SYNC_API_BASE_URL + endpoint, options);
                    if (retryResponse.status === 204) return true;
                    return await retryResponse.json();
                }
            }
            localStorage.clear();
            if (!window.location.pathname.includes("index.html") && !window.location.pathname.includes("forgot-password.html")) {
                const isInsideAdmin = window.location.pathname.includes("/admin/");
                window.location.href = isInsideAdmin ? "../index.html" : "index.html";
            }
            throw new Error("Session expired. Please log in again.");
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `Request failed: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Backend Sync Error:", error);
        throw error;
    }
}

// Check auth state on protected pages
function checkAuthentication() {
    const token = localStorage.getItem("pokemonNexusAccess") || localStorage.getItem("pokemonNexusToken");
    const isAuthPage = window.location.pathname.endsWith("index.html") || window.location.pathname.endsWith("forgot-password.html");
    if (!token && !isAuthPage) {
        // Handle admin subdirectory pathing
        if (window.location.pathname.includes("/admin/")) {
            window.location.href = "../index.html";
        } else {
            window.location.href = "index.html";
        }
    }
}

// ----------------------------------------------------
// PAGE SPECIFIC INTEGRATIONS
// ----------------------------------------------------

// 1. Pokedex & Party Integration
async function syncPokedexFromBackend() {
    try {
        const data = await syncApiRequest("/pokemon/?is_in_party=true");
        if (data && data.results) {
            const borderColors = {
                electric: "#ffcb05", fire: "#f97316", water: "#3b82f6", grass: "#10b981",
                psychic: "#ec4899", fighting: "#0ea5e9", dragon: "#a855f7", ice: "#67e8f9",
                steel: "#94a3b8", ground: "#b45309", rock: "#78350f", ghost: "#6366f1", poison: "#a855f7", bug: "#84cc16",
                fairy: "#ec4899", normal: "#9ca3af", flying: "#a78bfa", bug: "#84cc16", dark: "#4b5563"
            };
            const team = data.results.map(p => {
                const type1 = p.type1 ? p.type1.charAt(0).toUpperCase() + p.type1.slice(1).toLowerCase() : "Normal";
                const type2 = p.type2 ? p.type2.charAt(0).toUpperCase() + p.type2.slice(1).toLowerCase() : null;
                const border = borderColors[type1.toLowerCase()] || "#9ca3af";
                const types = type2 ? [type1, type2] : [type1];
                return {
                    id: p.pokedex_number,
                    pokedex_number: p.pokedex_number,
                    name: p.name,
                    level: p.level,
                    lvl: p.level,
                    dbId: p.id,
                    type: type1,
                    type1: type1,
                    type2: type2,
                    types: types,
                    border: border,
                    hp: p.hp,
                    maxHp: p.max_hp,
                    max_hp: p.max_hp,
                    moves: p.moves || [],
                    image: p.image || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${p.pokedex_number}.png`,
                    shiny: p.shiny || false
                };
            });
            localStorage.setItem("pokemonNexusTeam", JSON.stringify(team));
            console.log("Party synchronized from database:", team);
        }
    } catch (e) {
        console.error("Failed to sync party from database:", e);
    }
}

async function addPokemonToBackend(pokemonName) {
    if (!window.pokemonList) return;
    const details = window.pokemonList.find(x => x.name.toLowerCase() === pokemonName.toLowerCase());
    if (!details) {
        showToast("Error locating Pokémon stats.");
        return;
    }

    const type1 = details.types && details.types[0] ? details.types[0] : "Normal";
    const type2 = details.types && details.types[1] ? details.types[1] : null;
    const hp = details.stats && details.stats.hp ? details.stats.hp : 100;
    const attack = details.stats && details.stats.attack ? details.stats.attack : 80;
    const defense = details.stats && details.stats.defense ? details.stats.defense : 80;
    const speed = details.stats && details.stats.speed ? details.stats.speed : 80;
    const special_attack = details.stats && details.stats.special_attack ? details.stats.special_attack : 80;
    const special_defense = details.stats && details.stats.special_defense ? details.stats.special_defense : 80;

    const payload = {
        pokedex_number: details.id,
        name: details.name,
        type1: type1,
        type2: type2,
        rarity: details.rarity || "Common",
        level: Math.floor(Math.random() * 50) + 15,
        hp: hp,
        max_hp: hp,
        attack: attack,
        defense: defense,
        speed: speed,
        special_attack: special_attack,
        special_defense: special_defense,
        nature: "Hardy",
        ability: details.abilities && details.abilities.length > 0 ? details.abilities[0] : "Overgrow",
        moves: details.moves ? details.moves.slice(0, 4).map(m => ({name: m, type: type1, pp: "15/15"})) : [
            {name: "Tackle", type: "Normal", pp: "35/35"},
            {name: "Growl", type: "Normal", pp: "40/40"}
        ],
        image: details.img || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${details.id}.png`,
        shiny: Math.random() < 0.05,
        is_in_party: true
    };

    try {
        await syncApiRequest("/pokemon/", "POST", payload);
        showToast(`${pokemonName} successfully joined your battle roster!`);
        await syncPokedexFromBackend();
    } catch (err) {
        showToast(err.message || "Failed to add Pokémon to party.");
    }
}

window.replacePokemonInBackend = async function(oldDbId, newPokemonName) {
    let oldToggled = false;
    try {
        if (oldDbId) {
            await syncApiRequest("/pokemon/" + oldDbId + "/toggle-party/", "POST");
            oldToggled = true;
            console.log(`Backend: Removed Pokemon ID ${oldDbId} from party.`);
        }
        
        const localPokedexStr = localStorage.getItem('pokemonNexus_pokedex_152');
        let details = null;
        if (localPokedexStr) {
            try {
                const localPokedex = JSON.parse(localPokedexStr);
                details = localPokedex.find(x => x.name.toLowerCase() === newPokemonName.toLowerCase());
            } catch (e) {}
        }
        if (!details && window.pokemonList) {
            details = window.pokemonList.find(x => x.name.toLowerCase() === newPokemonName.toLowerCase());
        }
        if (!details) {
            throw new Error("Unable to locate Pokémon stats for backend sync.");
        }

        const type1 = details.types && details.types[0] ? details.types[0] : "Normal";
        const type2 = details.types && details.types[1] ? details.types[1] : null;
        const hp = details.hp || details.stats?.hp || 100;
        const attack = details.attack || details.stats?.attack || 80;
        const defense = details.defense || details.stats?.defense || 80;
        const speed = details.speed || details.stats?.speed || 80;
        const special_attack = details.spAtk || details.stats?.special_attack || 80;
        const special_defense = details.spDef || details.stats?.special_defense || 80;

        const payload = {
            pokedex_number: details.id,
            name: details.name,
            type1: type1,
            type2: type2,
            rarity: details.rarity || "Common",
            level: Math.floor(Math.random() * 50) + 15,
            hp: hp,
            max_hp: hp,
            attack: attack,
            defense: defense,
            speed: speed,
            special_attack: special_attack,
            special_defense: special_defense,
            nature: "Hardy",
            ability: details.abilities && details.abilities.length > 0 ? details.abilities[0] : "Overgrow",
            moves: details.moves ? details.moves.slice(0, 4).map(m => ({name: m, type: type1, pp: "15/15"})) : [
                {name: "Tackle", type: "Normal", pp: "35/35"},
                {name: "Growl", type: "Normal", pp: "40/40"}
            ],
            image: details.artwork || details.img || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${details.id}.png`,
            shiny: Math.random() < 0.05,
            is_in_party: true
        };
        
        const response = await syncApiRequest("/pokemon/", "POST", payload);
        if (response && response.id) {
            return response.id;
        }
        throw new Error("Invalid response from server.");
    } catch (e) {
        if (oldToggled && oldDbId) {
            try {
                await syncApiRequest("/pokemon/" + oldDbId + "/toggle-party/", "POST");
                console.log(`Backend: Reverted old Pokemon ID ${oldDbId} back into party.`);
            } catch (revertErr) {
                console.error("Critical: Failed to revert old Pokemon on backend:", revertErr);
            }
        }
        throw e;
    }
};

// 2. Inventory Integration
async function syncInventoryFromBackend() {
    try {
        const data = await syncApiRequest("/inventory/");
        if (data && Array.isArray(data)) {
            const dbItems = data;
            const localInv = window.inventory || [];
            
            dbItems.forEach(dbItem => {
                const localItem = localInv.find(x => x.name.toLowerCase() === dbItem.item_name.toLowerCase());
                if (localItem) {
                    localItem.qty = dbItem.quantity;
                }
            });
            localStorage.setItem("pokemonNexusInventory", JSON.stringify(localInv));
            console.log("Inventory synchronized from database.");
        }
    } catch (e) {
        console.error("Failed to sync inventory from database:", e);
    }
}

async function syncInventoryToBackend(inventory) {
    if (!inventory || !Array.isArray(inventory)) return;
    try {
        const payload = {
            items: inventory.map(x => ({
                id: x.id,
                name: x.name,
                category: x.category,
                qty: x.qty
            }))
        };
        await syncApiRequest("/inventory/sync/", "POST", payload);
        console.log("Inventory synced to database.");
    } catch (e) {
        console.error("Failed to sync inventory to database:", e);
    }
}

// 3. Kingdom Map Integration
async function syncMapFromBackend() {
    try {
        const data = await syncApiRequest("/regions/");
        if (data && Array.isArray(data)) {
            const dbRegions = data;
            const localRegions = window.dbRegions || [];
            
            dbRegions.forEach(dbReg => {
                const localReg = localRegions.find(x => x.id === dbReg.region_id);
                if (localReg) {
                    localReg.status = dbReg.status;
                    localReg.progress = dbReg.progress;
                    localReg.gyms = dbReg.gyms;
                }
            });
            localStorage.setItem("pokemonNexusMapData_v4", JSON.stringify(localRegions));
            console.log("Kingdom Map synchronized from database.");
        }
    } catch (e) {
        console.error("Failed to sync map from database:", e);
    }
}

async function syncMapToBackend(regions) {
    if (!regions || !Array.isArray(regions)) return;
    try {
        const payload = {
            regions: regions.map(x => ({
                id: x.id,
                name: x.name,
                status: x.status,
                progress: x.progress,
                gyms: x.gyms
            }))
        };
        await syncApiRequest("/regions/sync/", "POST", payload);
        console.log("Map synced to database.");
    } catch (e) {
        console.error("Failed to sync map to database:", e);
    }
}

// 4. Battle Screen Integration
async function syncBattleDataFromBackend() {
    try {
        // Initialize arrays on window object to prevent undefined errors
        if (!window.playerTeamData) {
            window.playerTeamData = [];
        }
        if (!window.bagItemsData) {
            window.bagItemsData = [];
        }

        const pokemonData = await syncApiRequest("/pokemon/?is_in_party=true");
        const results = pokemonData && pokemonData.results ? pokemonData.results : [];
        
        if (results.length > 0) {
            const team = results.map(p => {
                const borderColors = {
                    electric: "#ffcb05", fire: "#f97316", water: "#3b82f6", grass: "#10b981",
                    psychic: "#ec4899", fighting: "#0ea5e9", dragon: "#a855f7", ice: "#67e8f9",
                    steel: "#94a3b8", ground: "#b45309", rock: "#78350f", ghost: "#6366f1"
                };
                const type = p.type1 ? p.type1.toLowerCase() : "normal";
                const border = borderColors[type] || "#ffffff";
                
                return {
                    name: p.name,
                    lvl: p.level,
                    id: p.pokedex_number,
                    type: p.type1 || "Normal",
                    hp: p.hp,
                    maxHp: p.max_hp,
                    border: border,
                    moves: p.moves || []
                };
            });
            
            window.playerTeamData.length = 0;
            team.forEach(x => window.playerTeamData.push(x));
            console.log("Battle Team loaded from database:", window.playerTeamData);
        } else {
            window.playerTeamData.length = 0;
        }

        const invData = await syncApiRequest("/inventory/");
        const invArray = Array.isArray(invData) ? invData : [];
        
        const bag = invArray
            .filter(x => x && (x.category === "Potions" || x.category === "Poké Balls" || x.category === "Battle Items"))
            .map(x => ({
                name: x.item_name,
                qty: x.quantity,
                desc: "Drawn from inventory"
            }));
            
        window.bagItemsData.length = 0;
        if (bag.length > 0) {
            bag.forEach(x => window.bagItemsData.push(x));
        }
        console.log("Battle Items loaded from database:", window.bagItemsData);
    } catch (e) {
        console.error("Failed to load battle data from database:", e);
    }
}

async function recordBattleToBackend(isPlayerFainted) {
    if (!window.opponentTeamData || !window.playerTeamData) return;
    const isWin = !isPlayerFainted;
    const activeOpponent = window.opponentTeamData[window.activeOpponentPkmnIndex];
    const activePlayer = window.playerTeamData[window.activePlayerPkmnIndex];
    const userStr = localStorage.getItem("pokemonNexusUser");
    let trainerName = "Ash Ketchum";
    let trainerId = null;
    if (userStr) {
        try {
            const parsedUser = JSON.parse(userStr);
            trainerName = parsedUser.trainerName || parsedUser.username || "Ash Ketchum";
            trainerId = parsedUser.id;
        } catch(e) {}
    }

    const payload = {
        opponent: activeOpponent ? activeOpponent.name : "Wild Pikachu",
        opponent_name: activeOpponent ? activeOpponent.name : "Wild Pikachu",
        arena: document.getElementById("arenaSelect")?.value || "Volcano Arena",
        weather: document.getElementById("weather-title-txt")?.textContent || "Sunny / Magma Storm",
        battle_type: "wild",
        winner: isWin ? trainerName : (activeOpponent ? activeOpponent.name : "Wild Pikachu"),
        loser: isWin ? (activeOpponent ? activeOpponent.name : "Wild Pikachu") : trainerName,
        winner_name: isWin ? trainerName : (activeOpponent ? activeOpponent.name : "Wild Pikachu"),
        trainer_id: trainerId,
        is_win: isWin,
        xp_gained: isWin ? 450 : 100,
        coins_gained: isWin ? 150 : 50,
        pokemon_used: activePlayer ? [activePlayer.name] : [],
        moves_used: [],
        items_used: [],
        stat_turns: 5,
        stat_damage_dealt: isWin ? 300 : 100,
        stat_damage_taken: isWin ? 100 : 250,
        stat_critical_hits: isWin ? 1 : 0
    };

    console.log("BATTLE_API_CALLED");
    console.log("PAYLOAD:", payload);

    try {
        const response = await syncApiRequest("/battles/", "POST", payload);
        if (response && response.trainer) {
            localStorage.setItem("pokemonNexusUser", JSON.stringify(response.trainer));
            console.log("RESPONSE:", response);
            console.log("UPDATED_WINS:", response.trainer.wins);
            
            // Show premium Battle Reward popup after victory
            if (isWin && response.battle_rewards) {
                showBattleRewardPopup(response.battle_rewards);
            }
        }
    } catch (e) {
        console.error("Failed to save battle outcome:", e);
    }
}

// 5. Leaderboard Integration
async function syncLeaderboardFromBackend() {
    try {
        const data = await syncApiRequest("/leaderboard");
        if (data && Array.isArray(data)) {
            const trainers = data.map(t => ({
                id: t.rank,
                name: t.trainer_name,
                level: t.level,
                xp: t.xp,
                wins: t.wins,
                losses: t.losses,
                winRate: t.winRate,
                region: t.region,
                tier: t.tier || t.current_rank,
                avatarSeed: t.avatar && t.avatar.includes("official-artwork/") ? t.avatar.split("/").pop().split(".")[0] : 25,
                historyDir: "up"
            }));
            
            window.dbTrainers.length = 0;
            trainers.forEach(x => window.dbTrainers.push(x));
            console.log("Leaderboard updated from database:", window.dbTrainers);
        }
    } catch (e) {
        console.error("Failed to fetch leaderboard from database:", e);
    }
}

// 6. Profile Integration
async function syncProfileFromBackend() {
    try {
        const data = await syncApiRequest("/auth/profile/");
        if (data && data.user) {
            localStorage.setItem("pokemonNexusUser", JSON.stringify(data.user));
            console.log("Profile updated from database.");
        }
    } catch (e) {
        console.error("Failed to sync profile from database:", e);
    }
}

async function syncProfileRewardsSummary() {
    try {
        const data = await syncApiRequest("/rewards/dashboard/");
        if (data) {
            const crystalsEl = document.getElementById("profile-crystals");
            const pointsEl = document.getElementById("profile-points");
            const streakEl = document.getElementById("profile-streak");
            if (crystalsEl) crystalsEl.textContent = data.total_crystals;
            if (pointsEl) pointsEl.textContent = data.reward_points;
            if (streakEl) streakEl.textContent = `${data.login_streak} / 30`;
        }
    } catch(e) {
        console.error("Failed to sync profile rewards summary:", e);
    }
}

// 7. Admin Dashboard Database Integration
async function syncAdminDataFromBackend() {
    try {
        console.log("Fetching admin data from database...");
        
        // 1. Stats & Analytics
        const statsData = await syncApiRequest("/admin/stats");
        if (statsData && statsData.stats) {
            const statBlocks = document.querySelectorAll("#section-dashboard .cards .card h3");
            // If they are on dashboard, update metrics
            if (statBlocks.length >= 6) {
                statBlocks[0].textContent = statsData.stats.totalUsers.toLocaleString();
                statBlocks[1].textContent = statsData.stats.activeUsersToday.toLocaleString();
                statBlocks[2].textContent = statsData.stats.totalBattles.toLocaleString();
                statBlocks[3].textContent = statsData.stats.totalCapturedPokemon.toLocaleString();
                statBlocks[4].textContent = statsData.stats.totalCoins.toLocaleString();
                statBlocks[5].textContent = window.missionsDb ? window.missionsDb.length.toLocaleString() : "4";
            }
        }

        // 2. Fetch Users -> trainersDb
        const users = await syncApiRequest("/users");
        if (users && Array.isArray(users)) {
            window.trainersDb.length = 0;
            users.forEach(u => {
                window.trainersDb.push({
                    id: u.id,
                    name: u.trainerName || u.username,
                    level: u.level || 1,
                    region: u.region || "Kanto",
                    status: u.is_active ? "Active" : "Banned",
                    rank: u.current_rank || "Bronze"
                });
            });
        }

        // 3. Fetch Captured Pokémon -> pokemonDb
        const pokemon = await syncApiRequest("/pokemon/");
        if (pokemon && pokemon.results) {
            window.pokemonDb.length = 0;
            pokemon.results.forEach(p => {
                window.pokemonDb.push({
                    id: p.id,
                    name: p.name,
                    type: p.type1,
                    level: p.level,
                    rarity: p.rarity,
                    hp: p.hp,
                    attack: p.attack,
                    sprite: p.image
                });
            });
        }

        // 4. Fetch Battles -> battlesDb
        const battles = await syncApiRequest("/battles/");
        if (battles && battles.results) {
            window.battlesDb.length = 0;
            battles.results.forEach(b => {
                window.battlesDb.push({
                    id: b.id,
                    trainer: b.trainer_name || "Trainer",
                    opponent: b.opponent,
                    winner: b.winner,
                    arena: b.arena,
                    duration: `${Math.floor(b.battle_duration / 60)}m ${b.battle_duration % 60}s`,
                    status: "Completed"
                });
            });
        }

        // 5. Fetch Shop Items -> shopDb
        const shop = await syncApiRequest("/shop/");
        if (shop && shop.results) {
            window.shopDb.length = 0;
            shop.results.forEach(item => {
                window.shopDb.push({
                    id: item.id,
                    item_id: item.item_id,
                    name: item.name,
                    price: item.price,
                    stock: item.stock === -1 ? 999 : item.stock,
                    category: item.category
                });
            });
        }

        // 6. Fetch Leaderboard -> leaderboardDb
        const lb = await syncApiRequest("/leaderboard");
        if (lb && Array.isArray(lb)) {
            window.leaderboardDb.length = 0;
            lb.slice(0, 5).forEach(l => {
                window.leaderboardDb.push({
                    rank: l.rank,
                    trainer: l.trainer_name,
                    xp: `${l.xp.toLocaleString()} XP`,
                    wins: l.wins,
                    rate: `${l.winRate}%`,
                    tier: l.tier || l.current_rank
                });
            });
        }

        // 7. Fetch Missions -> missionsDb
        const missions = await syncApiRequest("/admin/rewards/missions/");
        if (missions && Array.isArray(missions)) {
            window.missionsDb.length = 0;
            missions.forEach(m => {
                let rewardText = `${m.reward_xp} XP, ${m.reward_coins} Coins`;
                if (m.reward_items && Object.keys(m.reward_items).length > 0) {
                    const itemsText = Object.entries(m.reward_items).map(([k, v]) => `${v} ${k}`).join(", ");
                    rewardText += `, ${itemsText}`;
                }
                window.missionsDb.push({
                    id: m.id,
                    name: m.title,
                    reward: rewardText,
                    difficulty: m.type === "story" ? "mythic" : (m.type === "weekly" ? "hard" : (m.type === "special" ? "medium" : "easy")),
                    progress: 0,
                    status: "Active"
                });
            });
            // Update active missions count on card
            const statBlocks = document.querySelectorAll("#section-dashboard .cards .card h3");
            if (statBlocks.length >= 6) {
                statBlocks[5].textContent = window.missionsDb.length.toLocaleString();
            }
        }

        console.log("Admin Dashboard data synced successfully.");
    } catch (e) {
        console.error("Failed to sync Admin data from database:", e);
    }
}

// Admin CRUD Interceptor
function registerAdminInterceptors() {
    if (!window.location.pathname.endsWith("admin.html")) return;

    // 1. Intercept Modal confirmations
    if (window.openCustomModal) {
        const originalOpenCustomModal = window.openCustomModal;
        window.openCustomModal = function(title, bodyHtml, confirmCallback) {
            const wrappedCallback = async function() {
                // Execute original UI changes
                confirmCallback();

                // Sync new additions to backend
                try {
                    if (title.includes("Pokémon")) {
                        const newPkmn = window.pokemonDb[window.pokemonDb.length - 1];
                        const payload = {
                            pokedex_number: 1, // Default Pokedex number for custom creations
                            name: newPkmn.name,
                            type1: newPkmn.type,
                            level: newPkmn.level,
                            rarity: newPkmn.rarity,
                            hp: newPkmn.hp,
                            max_hp: newPkmn.hp,
                            attack: newPkmn.attack,
                            defense: 80, speed: 80, special_attack: 80, special_defense: 80,
                            image: newPkmn.sprite
                        };
                        await syncApiRequest("/pokemon/", "POST", payload);
                        showToast("Created Pokémon in backend database!");
                    } else if (title.includes("Shop") || title.includes("Item")) {
                        const newItem = window.shopDb[window.shopDb.length - 1];
                        const payload = {
                            item_id: Math.floor(Math.random() * 1000) + 100,
                            name: newItem.name,
                            description: "Admin added item",
                            category: newItem.category,
                            price: newItem.price,
                            stock: newItem.stock,
                            rarity: "Common",
                            image: "https://archives.bulbagarden.net/media/upload/7/79/Dream_Pok%C3%A9_Ball_Sprite.png"
                        };
                        await syncApiRequest("/shop/", "POST", payload);
                        showToast("Created Shop Item in backend database!");
                    } else if (title.includes("Mission")) {
                        const newMission = window.missionsDb[window.missionsDb.length - 1];
                        const payload = {
                            title: newMission.name,
                            description: newMission.name,
                            type: "daily",
                            reward_xp: 300,
                            reward_coins: 100
                        };
                        await syncApiRequest("/admin/rewards/missions/", "POST", payload);
                        showToast("Created Mission in backend database!");
                    }
                    // Refresh backend database state
                    await syncAdminDataFromBackend();
                    if (window.refreshSectionContent) {
                        const activeSec = document.querySelector(".admin-section.active-section");
                        if (activeSec) {
                            const secId = activeSec.id.replace("section-", "");
                            window.refreshSectionContent(secId);
                        }
                    }
                } catch (e) {
                    showToast("Failed to sync new item to database: " + e.message);
                }
            };

            originalOpenCustomModal(title, bodyHtml, wrappedCallback);
        };
    }

    // 2. Intercept Pokémon Deletion
    if (window.deletePokemon) {
        const originalDelete = window.deletePokemon;
        window.deletePokemon = async function(idx) {
            const target = window.pokemonDb[idx];
            if (target && target.id) {
                try {
                    await syncApiRequest(`/pokemon/${target.id}/`, "DELETE");
                    showToast("Deleted Pokémon from database!");
                    await syncAdminDataFromBackend();
                    if (window.refreshSectionContent) window.refreshSectionContent("pokemon");
                } catch (e) {
                    showToast("Failed to delete Pokémon from database: " + e.message);
                }
            }
            originalDelete(idx);
        };
    }

    // 3. Intercept Trainer Actions
    if (window.editTrainer) {
        const originalEditTrainer = window.editTrainer;
        window.editTrainer = function(idx) {
            const target = window.trainersDb[idx];
            const originalOpenModal = window.openCustomModal;
            
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    const originalData = { ...target };
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    if (target && target.id) {
                        try {
                            const payload = {
                                trainerName: target.name,
                                level: target.level,
                                region: target.region,
                                current_rank: target.rank
                            };
                            await syncApiRequest(`/auth/users/${target.id}/`, "PUT", payload);
                            showToast("Updated trainer in backend database!");
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                        } catch (e) {
                            Object.assign(target, originalData);
                            showToast("Failed to update trainer in database: " + e.message);
                            if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalEditTrainer(idx);
            window.openCustomModal = originalOpenModal;
        };
    }

    if (window.openAddTrainerModal) {
        const originalAddTrainer = window.openAddTrainerModal;
        window.openAddTrainerModal = function() {
            const originalOpenModal = window.openCustomModal;
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    const lengthBefore = window.trainersDb.length;
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    const newTrainer = window.trainersDb[window.trainersDb.length - 1];
                    if (newTrainer && window.trainersDb.length > lengthBefore) {
                        try {
                            const email = `${newTrainer.name.toLowerCase().replace(/[^a-z0-9]/g, "")}@pokemonnexus.com`;
                            const payload = {
                                trainerName: newTrainer.name,
                                email: email,
                                password: "trainerpass123",
                                confirmPassword: "trainerpass123",
                                role: "trainer"
                            };
                            const regRes = await syncApiRequest("/auth/register", "POST", payload);
                            if (regRes && regRes.user) {
                                const updatePayload = {
                                    level: newTrainer.level,
                                    region: newTrainer.region,
                                    current_rank: newTrainer.rank
                                };
                                await syncApiRequest(`/auth/users/${regRes.user.id}/`, "PUT", updatePayload);
                                showToast("Registered trainer in backend database!");
                            }
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                        } catch (e) {
                            window.trainersDb.pop();
                            showToast("Failed to register trainer on backend: " + e.message);
                            if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalAddTrainer();
            window.openCustomModal = originalOpenModal;
        };
    }

    if (window.toggleTrainerStatus) {
        const originalToggle = window.toggleTrainerStatus;
        window.toggleTrainerStatus = async function(idx) {
            const target = window.trainersDb[idx];
            if (target && target.id) {
                const originalStatus = target.status;
                const is_active = originalStatus !== "Active"; // target status is going to toggle
                
                // Mutate locally and show status changes
                target.status = is_active ? "Active" : "Banned";
                if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                
                try {
                    await syncApiRequest(`/auth/users/${target.id}/`, "PATCH", { is_active });
                    showToast(`Trainer status synchronized with database!`);
                    await syncAdminDataFromBackend();
                    if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                } catch (e) {
                    target.status = originalStatus;
                    showToast("Failed to update status on backend: " + e.message);
                    if (window.refreshSectionContent) window.refreshSectionContent("trainers");
                }
            } else {
                originalToggle(idx);
            }
        };
    }

    // 4. Intercept Shop Item Actions
    if (window.editShopItem) {
        const originalEditShopItem = window.editShopItem;
        window.editShopItem = function(idx) {
            const target = window.shopDb[idx];
            const originalOpenModal = window.openCustomModal;
            
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    const originalData = { ...target };
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    if (target && target.id) {
                        try {
                            const payload = {
                                name: target.name,
                                price: target.price,
                                stock: target.stock,
                                category: target.category
                            };
                            await syncApiRequest(`/shop/${target.id}/`, "PUT", payload);
                            showToast("Updated Shop Item in database!");
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("shop");
                        } catch (e) {
                            Object.assign(target, originalData);
                            showToast("Failed to update Shop Item: " + e.message);
                            if (window.refreshSectionContent) window.refreshSectionContent("shop");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalEditShopItem(idx);
            window.openCustomModal = originalOpenModal;
        };
    }

    if (window.deleteShopItem) {
        const originalDeleteShopItem = window.deleteShopItem;
        window.deleteShopItem = function(idx) {
            const target = window.shopDb[idx];
            const originalOpenModal = window.openCustomModal;
            
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    if (target && target.id) {
                        try {
                            await syncApiRequest(`/shop/${target.id}/`, "DELETE");
                            showToast("Deleted Shop Item from database!");
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("shop");
                        } catch (e) {
                            showToast("Failed to delete Shop Item: " + e.message);
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("shop");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalDeleteShopItem(idx);
            window.openCustomModal = originalOpenModal;
        };
    }

    // 5. Intercept Mission Actions
    if (window.openAddMissionModal) {
        const originalAddMission = window.openAddMissionModal;
        window.openAddMissionModal = function() {
            const originalOpenModal = window.openCustomModal;
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    const lengthBefore = window.missionsDb.length;
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    const newMission = window.missionsDb[window.missionsDb.length - 1];
                    if (newMission && window.missionsDb.length > lengthBefore) {
                        try {
                            const payload = {
                                title: newMission.name,
                                description: newMission.name,
                                type: newMission.difficulty === "mythic" ? "story" : (newMission.difficulty === "hard" ? "weekly" : (newMission.difficulty === "medium" ? "special" : "daily")),
                                reward_xp: 300,
                                reward_coins: 100
                            };
                            await syncApiRequest("/admin/rewards/missions/", "POST", payload);
                            showToast("Created Mission in database!");
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("missions");
                        } catch (e) {
                            window.missionsDb.pop();
                            showToast("Failed to create Mission: " + e.message);
                            if (window.refreshSectionContent) window.refreshSectionContent("missions");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalAddMission();
            window.openCustomModal = originalOpenModal;
        };
    }

    if (window.editMission) {
        const originalEditMission = window.editMission;
        window.editMission = function(idx) {
            const target = window.missionsDb[idx];
            const originalOpenModal = window.openCustomModal;
            
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    const originalData = { ...target };
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    if (target && target.id) {
                        try {
                            const payload = {
                                title: target.name,
                                description: target.name,
                                type: target.difficulty === "mythic" ? "story" : (target.difficulty === "hard" ? "weekly" : (target.difficulty === "medium" ? "special" : "daily")),
                                reward_xp: 300,
                                reward_coins: 100
                            };
                            await syncApiRequest(`/admin/rewards/missions/${target.id}/`, "PUT", payload);
                            showToast("Updated Mission in database!");
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("missions");
                        } catch (e) {
                            Object.assign(target, originalData);
                            showToast("Failed to update Mission: " + e.message);
                            if (window.refreshSectionContent) window.refreshSectionContent("missions");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalEditMission(idx);
            window.openCustomModal = originalOpenModal;
        };
    }

    if (window.deleteMission) {
        const originalDeleteMission = window.deleteMission;
        window.deleteMission = function(idx) {
            const target = window.missionsDb[idx];
            const originalOpenModal = window.openCustomModal;
            
            window.openCustomModal = function(title, bodyHtml, confirmCallback) {
                const wrappedConfirm = async function() {
                    confirmCallback();
                    window.openCustomModal = originalOpenModal;
                    
                    if (target && target.id) {
                        try {
                            await syncApiRequest(`/admin/rewards/missions/${target.id}/`, "DELETE");
                            showToast("Deleted Mission from database!");
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("missions");
                        } catch (e) {
                            showToast("Failed to delete Mission: " + e.message);
                            await syncAdminDataFromBackend();
                            if (window.refreshSectionContent) window.refreshSectionContent("missions");
                        }
                    }
                };
                originalOpenModal(title, bodyHtml, wrappedConfirm);
            };
            originalDeleteMission(idx);
            window.openCustomModal = originalOpenModal;
        };
    }
}

// ----------------------------------------------------
// SCRIPT WRAPPERS & HOOKS INJECTION
// ----------------------------------------------------
checkAuthentication();

// --- PREMIUM CLAIM ANIMATIONS & SOUND SYNTHESIS ---

function injectRewardsStyles() {
    if (document.getElementById("rewards-animation-styles")) return;
    
    const styleSheet = document.createElement("style");
    styleSheet.id = "rewards-animation-styles";
    styleSheet.innerText = `
        @keyframes reward-glow {
          0% { box-shadow: 0 0 15px rgba(255, 203, 5, 0.4), inset 0 0 15px rgba(255, 203, 5, 0.2); }
          50% { box-shadow: 0 0 45px rgba(255, 203, 5, 0.85), inset 0 0 30px rgba(255, 203, 5, 0.4); }
          100% { box-shadow: 0 0 15px rgba(255, 203, 5, 0.4), inset 0 0 15px rgba(255, 203, 5, 0.2); }
        }
        @keyframes reward-pop {
          0% { transform: scale(0.6) rotate(-10deg); opacity: 0; }
          70% { transform: scale(1.1) rotate(5deg); opacity: 1; }
          100% { transform: scale(1) rotate(0deg); }
        }
        @keyframes particle-fly {
          0% { transform: translate(0, 0) scale(1); opacity: 1; }
          100% { transform: translate(var(--dx), var(--dy)) scale(0); opacity: 0; }
        }
        .reward-overlay-screen {
          position: fixed;
          inset: 0;
          background: rgba(4, 7, 20, 0.92);
          backdrop-filter: blur(10px);
          z-index: 100000;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          opacity: 0;
          transition: opacity 0.4s ease;
          pointer-events: none;
        }
        .reward-overlay-screen.show {
          opacity: 1;
          pointer-events: auto;
        }
        .reward-container-box {
          text-align: center;
          animation: reward-pop 0.65s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }
        .reward-chest-glow {
          width: 130px;
          height: 130px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(255, 203, 5, 0.35) 0%, transparent 70%);
          display: flex;
          align-items: center;
          justify-content: center;
          animation: reward-glow 2s infinite;
          margin: 0 auto 24px;
        }
        .reward-icon-large {
          font-size: 72px;
          filter: drop-shadow(0 0 18px rgba(255, 203, 5, 0.7));
          user-select: none;
        }
        .reward-title-text {
          font-family: 'Fredoka', sans-serif;
          font-size: 2.4rem;
          color: var(--yellow);
          text-shadow: 0 0 20px rgba(255, 203, 5, 0.6);
          margin: 0 0 12px 0;
          letter-spacing: 1px;
        }
        .reward-subtitle-text {
          font-size: 1.25rem;
          font-weight: 700;
          color: #fff;
          margin: 0;
          letter-spacing: 0.5px;
        }
        .reward-particle {
          position: absolute;
          width: 9px;
          height: 9px;
          background: var(--yellow);
          border-radius: 50%;
          pointer-events: none;
          box-shadow: 0 0 12px var(--yellow);
          z-index: 100001;
        }
    `;
    document.head.appendChild(styleSheet);

    const overlay = document.createElement("div");
    overlay.id = "reward-overlay-screen";
    overlay.className = "reward-overlay-screen";
    overlay.innerHTML = `
      <div class="reward-container-box">
        <div class="reward-chest-glow">
          <div class="reward-icon-large" id="reward-icon-large">🪙</div>
        </div>
        <h2 class="reward-title-text">REWARD CLAIMED!</h2>
        <p class="reward-subtitle-text" id="reward-subtitle-text">+100 Coins</p>
      </div>
    `;
    document.body.appendChild(overlay);
}

function playRewardChimeSound() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
            setTimeout(() => {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                
                osc.type = "sine";
                osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
                
                gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.9);
                
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                
                osc.start();
                osc.stop(audioCtx.currentTime + 0.95);
            }, idx * 100);
        });
    } catch(e) {
        console.warn("Audio synthesis block:", e);
    }
}

function explodeRewardParticles() {
    const overlay = document.getElementById("reward-overlay-screen");
    if (!overlay) return;
    
    for (let i = 0; i < 40; i++) {
        const p = document.createElement("div");
        p.className = "reward-particle";
        
        const angle = Math.random() * Math.PI * 2;
        const dist = 110 + Math.random() * 220;
        const dx = Math.cos(angle) * dist;
        const dy = Math.sin(angle) * dist;
        
        p.style.setProperty("--dx", `${dx}px`);
        p.style.setProperty("--dy", `${dy}px`);
        
        const isGold = Math.random() > 0.35;
        p.style.background = isGold ? "var(--yellow)" : "var(--green)";
        p.style.boxShadow = `0 0 10px ${isGold ? 'var(--yellow)' : 'var(--green)'}`;
        
        const duration = 0.75 + Math.random() * 0.75;
        p.style.animation = `particle-fly ${duration}s cubic-bezier(0.1, 0.8, 0.25, 1) forwards`;
        
        overlay.appendChild(p);
        setTimeout(() => p.remove(), duration * 1000);
    }
}

function displayClaimPopupAnimation(reward) {
    injectRewardsStyles();
    
    const overlay = document.getElementById("reward-overlay-screen");
    const iconEl = document.getElementById("reward-icon-large");
    const textEl = document.getElementById("reward-subtitle-text");
    
    if (!overlay || !iconEl || !textEl) return;
    
    let icon = "🎁";
    let rewardText = "";
    
    if (reward.type === "Coins") {
        icon = "🪙";
        rewardText = `+${reward.amount} Poké Coins`;
    } else if (reward.type === "Crystals") {
        icon = "💎";
        rewardText = `+${reward.amount} Crystals`;
    } else if (reward.type === "XP") {
        icon = "🎫";
        rewardText = `+${reward.amount} XP`;
    } else if (reward.type === "Item") {
        icon = "📦";
        rewardText = `${reward.item_name} x${reward.amount}`;
    }
    
    iconEl.textContent = icon;
    textEl.textContent = rewardText;
    
    overlay.classList.add("show");
    playRewardChimeSound();
    explodeRewardParticles();
    
    setTimeout(() => {
        overlay.classList.remove("show");
        showToast(`Successfully claimed Daily Reward: ${rewardText}!`);
    }, 2500);
}

async function claimDailyReward() {
    const btn = document.getElementById("btn-claim-daily");
    if (!btn || btn.disabled) return;
    
    btn.disabled = true;
    btn.textContent = "CLAIMING...";
    
    try {
        const res = await syncApiRequest("/rewards/daily/claim/", "POST");
        if (res && res.reward) {
            displayClaimPopupAnimation(res.reward);
            
            setTimeout(async () => {
                await syncRewardsDataFromBackend();
                
                const profileData = await syncApiRequest("/auth/profile/");
                if (profileData && profileData.user) {
                    localStorage.setItem("pokemonNexusUser", JSON.stringify(profileData.user));
                    const navName = document.getElementById("nav-trainer-name");
                    const navLvl = document.getElementById("nav-trainer-level");
                    const welcome = document.getElementById("trainerWelcome");
                    if (navName) navName.textContent = profileData.user.trainerName || "Trainer";
                    if (navLvl) navLvl.textContent = "Level " + (profileData.user.level || 1);
                    if (welcome) welcome.textContent = "Welcome, " + (profileData.user.trainerName || "Trainer") + "!";
                }
            }, 2500);
        }
    } catch(e) {
        showToast(e.message || "Failed to claim daily reward.");
        btn.disabled = false;
        btn.textContent = "Claim Daily Reward";
    }
}

// --- PREMIUM BATTLE REWARDS POPUP ---

function injectBattleRewardsStyles() {
    if (document.getElementById("battle-rewards-popup-styles")) return;
    
    const styleSheet = document.createElement("style");
    styleSheet.id = "battle-rewards-popup-styles";
    styleSheet.innerText = `
        @keyframes battle-pop {
          0% { transform: translate(-50%, -50%) scale(0.7); opacity: 0; }
          75% { transform: translate(-50%, -50%) scale(1.05); opacity: 1; }
          100% { transform: translate(-50%, -50%) scale(1); }
        }
        .battle-reward-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.85);
          backdrop-filter: blur(8px);
          z-index: 999999;
          opacity: 0;
          transition: opacity 0.3s ease;
          pointer-events: none;
        }
        .battle-reward-overlay.show {
          opacity: 1;
          pointer-events: auto;
        }
        .battle-reward-popup {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: min(420px, 90vw);
          background: rgba(6, 11, 28, 0.95);
          border: 2px solid var(--green);
          box-shadow: 0 0 35px rgba(41, 255, 182, 0.35);
          border-radius: 20px;
          padding: 24px;
          text-align: center;
          z-index: 1000000;
          animation: battle-pop 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }
        .battle-reward-header {
          font-family: 'Fredoka', sans-serif;
          font-size: 1.8rem;
          color: var(--yellow);
          -webkit-text-stroke: 1px #0757a8;
          text-shadow: 0 0 15px rgba(255, 203, 5, 0.6);
          margin: 0 0 4px 0;
          text-transform: uppercase;
        }
        .battle-reward-subheader {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 20px;
        }
        .battle-reward-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-bottom: 20px;
        }
        .battle-reward-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 12px 6px;
          text-align: center;
          transition: all 0.2s;
        }
        .battle-reward-card:hover {
          border-color: rgba(12, 112, 255, 0.4);
          transform: translateY(-2px);
        }
        .battle-reward-lbl {
          font-size: 0.62rem;
          color: rgba(255, 255, 255, 0.5);
          text-transform: uppercase;
          font-weight: 700;
          margin-bottom: 4px;
        }
        .battle-reward-ico {
          font-size: 22px;
          margin-bottom: 4px;
        }
        .battle-reward-val {
          font-size: 0.85rem;
          font-weight: 800;
        }
        .battle-item-drop-box {
          background: linear-gradient(135deg, rgba(255, 203, 5, 0.1), rgba(12, 112, 255, 0.05));
          border: 1px dashed var(--yellow);
          border-radius: 14px;
          padding: 12px;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
        }
        .battle-item-drop-box img {
          width: 36px;
          height: 36px;
          object-fit: contain;
        }
        .battle-item-drop-info {
          text-align: left;
        }
        .battle-item-drop-title {
          font-size: 0.85rem;
          font-weight: 800;
          color: #fff;
        }
        .battle-item-drop-desc {
          font-size: 0.68rem;
          color: rgba(255, 255, 255, 0.55);
        }
        .btn-battle-continue {
          flex: 1;
          background: linear-gradient(135deg, var(--green), var(--blue));
          border: none;
          color: #061225;
          font-weight: 900;
          padding: 12px;
          border-radius: 12px;
          cursor: pointer;
          font-size: 0.85rem;
          text-transform: uppercase;
          transition: all 0.2s;
        }
        .btn-battle-continue:hover {
          box-shadow: 0 0 15px rgba(41, 255, 182, 0.4);
          transform: translateY(-1px);
        }
        .btn-battle-home {
          flex: 1;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: white;
          font-weight: 700;
          padding: 12px;
          border-radius: 12px;
          cursor: pointer;
          font-size: 0.85rem;
          text-transform: uppercase;
          transition: all 0.2s;
        }
        .btn-battle-home:hover {
          background: rgba(255, 255, 255, 0.15);
          transform: translateY(-1px);
        }
    `;
    document.head.appendChild(styleSheet);

    const overlay = document.createElement("div");
    overlay.id = "battle-reward-overlay";
    overlay.className = "battle-reward-overlay";
    overlay.innerHTML = `
      <div class="battle-reward-popup">
        <h2 class="battle-reward-header">Victory!</h2>
        <div class="battle-reward-subheader">Battle rewards secured from server</div>
        
        <div class="battle-reward-grid">
          <div class="battle-reward-card">
            <div class="battle-reward-lbl">Coins</div>
            <div class="battle-reward-ico">🪙</div>
            <div class="battle-reward-val" id="battle-rew-coins">+0</div>
          </div>
          <div class="battle-reward-card">
            <div class="battle-reward-lbl">XP</div>
            <div class="battle-reward-ico">🎫</div>
            <div class="battle-reward-val" id="battle-rew-xp">+0</div>
          </div>
          <div class="battle-reward-card">
            <div class="battle-reward-lbl">Points</div>
            <div class="battle-reward-ico">💎</div>
            <div class="battle-reward-val" id="battle-rew-points">+0</div>
          </div>
        </div>
        
        <div class="battle-item-drop-box" id="battle-item-drop-box" style="display:none">
          <img src="" id="battle-item-drop-img" />
          <div class="battle-item-drop-info">
            <div class="battle-item-drop-title" id="battle-item-drop-title">Poke Ball</div>
            <div class="battle-item-drop-desc">Lucky Chance Item Drop Unlocked!</div>
          </div>
        </div>
        
        <div class="battle-reward-buttons" style="display: flex; gap: 12px; margin-top: 20px;">
          <button class="btn-battle-continue" id="btn-battle-continue">Continue Battle</button>
          <button class="btn-battle-home" id="btn-battle-home">Return Home</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
}

function showBattleRewardPopup(rewards) {
    injectBattleRewardsStyles();
    
    const overlay = document.getElementById("battle-reward-overlay");
    const coinsEl = document.getElementById("battle-rew-coins");
    const xpEl = document.getElementById("battle-rew-xp");
    const pointsEl = document.getElementById("battle-rew-points");
    const itemBox = document.getElementById("battle-item-drop-box");
    const itemImg = document.getElementById("battle-item-drop-img");
    const itemTitle = document.getElementById("battle-item-drop-title");
    const continueBtn = document.getElementById("btn-battle-continue");
    const homeBtn = document.getElementById("btn-battle-home");
    
    if (!overlay) return;
    
    if (coinsEl) coinsEl.textContent = `+${rewards.coins || 0}`;
    if (xpEl) xpEl.textContent = `+${rewards.xp || 0}`;
    if (pointsEl) pointsEl.textContent = `+${rewards.reward_points || 0}`;
    
    if (rewards.item && itemBox && itemImg && itemTitle) {
        const itemIcons = {
            "Poke Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png",
            "Great Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/great-ball.png",
            "Ultra Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/ultra-ball.png",
            "Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/potion.png",
            "Rare Candy": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/rare-candy.png",
            "Fire Stone": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/fire-stone.png"
        };
        const iconUrl = itemIcons[rewards.item.name] || "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png";
        
        itemImg.src = iconUrl;
        itemTitle.textContent = `${rewards.item.name} x${rewards.item.amount}`;
        itemBox.style.display = "flex";
    } else if (itemBox) {
        itemBox.style.display = "none";
    }
    
    overlay.classList.add("show");
    playRewardChimeSound();
    
    if (continueBtn) {
        continueBtn.onclick = () => {
            overlay.classList.remove("show");
            if (typeof window.resetBattleGame === "function") {
                window.resetBattleGame();
            } else {
                window.location.reload();
            }
        };
    }
    if (homeBtn) {
        homeBtn.onclick = () => {
            overlay.classList.remove("show");
            window.location.href = "index.html";
        };
    }
}

// --- PREMIUM MISSION REWARDS INTEGRATION ---

async function syncMissionsFromBackend() {
    try {
        const data = await syncApiRequest("/missions/");
        if (data && Array.isArray(data)) {
            window.activeMissionsDb = data; // Cache globally
            renderMissionsList("all");
        }
    } catch(e) {
        console.error("Failed to sync missions:", e);
    }
}

window.filterMissionsByType = function(type) {
    renderMissionsList(type);
};

function renderMissionsList(typeFilter = "all") {
    const container = document.getElementById("missions-container");
    if (!container || !window.activeMissionsDb) return;
    
    container.innerHTML = "";
    
    const filtered = window.activeMissionsDb.filter(m => {
        if (typeFilter === "all") return true;
        return m.mission_type.toLowerCase() === typeFilter.toLowerCase();
    });
    
    if (filtered.length === 0) {
        container.innerHTML = `<div style="text-align:center;color:rgba(255,255,255,0.3);padding:24px 0;">No active ${typeFilter} missions.</div>`;
        return;
    }
    
    const itemIcons = {
        "Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/potion.png",
        "Super Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/super-potion.png",
        "Hyper Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/hyper-potion.png",
        "Max Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/max-potion.png",
        "Poke Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png",
        "Great Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/great-ball.png",
        "Ultra Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/ultra-ball.png",
        "Master Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png",
        "Rare Candy": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/rare-candy.png",
        "Fire Stone": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/fire-stone.png",
        "Water Stone": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/water-stone.png",
        "Thunder Stone": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/thunder-stone.png",
        "Leaf Stone": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/leaf-stone.png"
    };

    filtered.forEach(m => {
        const item = document.createElement("div");
        item.className = `milestone-item ${m.claimable && !m.claimed ? 'claimable' : ''}`;
        
        const pct = Math.min(100, Math.floor((m.current_progress / m.required_progress) * 100));
        
        let rewardDesc = "";
        if (m.reward_coins > 0) rewardDesc += `🪙 +${m.reward_coins} `;
        if (m.reward_xp > 0) rewardDesc += `🎫 +${m.reward_xp} `;
        
        const r_items = m.reward_items || {};
        Object.entries(r_items).forEach(([name, qty]) => {
            if (name.toLowerCase() === 'crystals') {
                rewardDesc += `💎 +${qty} `;
            } else if (name.toLowerCase() in ['reward points', 'reward_points']) {
                rewardDesc += `⭐ +${qty} `;
            } else {
                const icon = itemIcons[name] ? `<img src="${itemIcons[name]}" style="width:16px;height:16px;vertical-align:middle;margin-right:2px;" />` : "";
                rewardDesc += `${icon}${name} x${qty} `;
            }
        });
        
        let btnText = "In Progress";
        let btnClass = "";
        let btnDisabled = true;
        
        if (m.claimed) {
            btnText = "Claimed";
            btnClass = "disabled";
        } else if (m.claimable) {
            btnText = "Claim";
            btnClass = "claimable";
            btnDisabled = false;
        } else {
            btnText = `${pct}%`;
        }
        
        let typeBadge = "🎯";
        if (m.mission_type.toLowerCase() === "weekly") typeBadge = "📅";
        else if (m.mission_type.toLowerCase() === "story") typeBadge = "🏆";
        else if (m.mission_type.toLowerCase() === "special") typeBadge = "🔥";
        
        item.innerHTML = `
            <div class="milestone-left" style="flex:1;">
                <div class="level-badge" style="background:#1e293b;border-color:var(--border-neon);">
                    <val style="font-size:1.25rem">${typeBadge}</val>
                </div>
                <div class="milestone-info" style="flex:1;">
                    <div class="milestone-reward-desc">${m.title}</div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.6);margin-bottom:6px;">${m.description}</div>
                    <div class="profile-xp-progress" style="height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden;margin-bottom:6px;width:80%;">
                        <div class="profile-xp-fill" style="width:${pct}%;height:100%;background:linear-gradient(90deg,var(--green),var(--blue));"></div>
                    </div>
                    <div class="milestone-reward-sub" style="font-size:0.68rem;color:var(--yellow);">${rewardDesc}</div>
                </div>
            </div>
            <button class="btn-milestone-claim ${btnClass}" ${btnDisabled ? 'disabled' : ''} onclick="claimMissionReward(${m.id})">${btnText}</button>
        `;
        container.appendChild(item);
    });
}

window.claimMissionReward = async function(progressId) {
    const buttons = document.querySelectorAll(`button[onclick="claimMissionReward(${progressId})"]`);
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.textContent = "Claiming...";
    });
    
    try {
        const response = await syncApiRequest(`/missions/${progressId}/claim/`, "POST");
        if (response && response.rewards) {
            displayMissionsPopupAnimation({
                amount: response.rewards.coins,
                xp: response.rewards.xp,
                items: response.rewards.items
            });
            
            setTimeout(async () => {
                await syncRewardsDataFromBackend();
                await syncMissionsFromBackend();
                
                const profileData = await syncApiRequest("/auth/profile/");
                if (profileData && profileData.user) {
                    localStorage.setItem("pokemonNexusUser", JSON.stringify(profileData.user));
                    const navName = document.getElementById("nav-trainer-name");
                    const navLvl = document.getElementById("nav-trainer-level");
                    const welcome = document.getElementById("trainerWelcome");
                    if (navName) navName.textContent = profileData.user.trainerName || "Trainer";
                    if (navLvl) navLvl.textContent = "Level " + (profileData.user.level || 1);
                    if (welcome) welcome.textContent = "Welcome, " + (profileData.user.trainerName || "Trainer") + "!";
                }
            }, 3000);
        }
    } catch(e) {
        showToast(e.message || "Failed to claim mission reward.");
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.textContent = "Claim";
        });
    }
};

window.claimLevelMilestone = async function(level) {
    const btn = document.querySelector(`button[onclick="claimLevelMilestone(${level})"]`);
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Claiming...";
    }
    try {
        const res = await syncApiRequest("/rewards/level/claim/", "POST", { level: level });
        if (res && res.reward) {
            displayClaimPopupAnimation(res.reward);
            setTimeout(async () => {
                await syncRewardsDataFromBackend();
                const profileData = await syncApiRequest("/auth/profile/");
                if (profileData && profileData.user) {
                    localStorage.setItem("pokemonNexusUser", JSON.stringify(profileData.user));
                    const navName = document.getElementById("nav-trainer-name");
                    const navLvl = document.getElementById("nav-trainer-level");
                    const welcome = document.getElementById("trainerWelcome");
                    if (navName) navName.textContent = profileData.user.trainerName || "Trainer";
                    if (navLvl) navLvl.textContent = "Level " + (profileData.user.level || 1);
                    if (welcome) welcome.textContent = "Welcome, " + (profileData.user.trainerName || "Trainer") + "!";
                }
            }, 2500);
        }
    } catch(e) {
        showToast(e.message || "Failed to claim level milestone.");
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Claim";
        }
    }
};

window.claimEventReward = async function(eventId) {
    const btn = document.querySelector(`button[onclick="claimEventReward(${eventId})"]`);
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Claiming...";
    }
    try {
        const res = await syncApiRequest("/rewards/events/claim/", "POST", { event_id: eventId });
        if (res && res.reward) {
            displayClaimPopupAnimation(res.reward);
            setTimeout(async () => {
                await syncRewardsDataFromBackend();
                const profileData = await syncApiRequest("/auth/profile/");
                if (profileData && profileData.user) {
                    localStorage.setItem("pokemonNexusUser", JSON.stringify(profileData.user));
                    const navName = document.getElementById("nav-trainer-name");
                    const navLvl = document.getElementById("nav-trainer-level");
                    const welcome = document.getElementById("trainerWelcome");
                    if (navName) navName.textContent = profileData.user.trainerName || "Trainer";
                    if (navLvl) navLvl.textContent = "Level " + (profileData.user.level || 1);
                    if (welcome) welcome.textContent = "Welcome, " + (profileData.user.trainerName || "Trainer") + "!";
                }
            }, 2500);
        }
    } catch(e) {
        showToast(e.message || "Failed to claim event reward.");
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Claim";
        }
    }
};

function displayMissionsPopupAnimation(rewards) {
    injectRewardsStyles();
    
    const overlay = document.getElementById("reward-overlay-screen");
    if (!overlay) return;
    
    const box = overlay.querySelector(".reward-container-box");
    if (!box) return;
    
    const hasMysteryChest = rewards.items && (rewards.items["Mystery Chest"] || rewards.items["mystery_chest"]);
    let chestHtml = `<div class="reward-icon-large">🎁</div>`;
    if (hasMysteryChest) {
        chestHtml = `
            <div class="reward-icon-large" id="chest-animation-icon" style="transition: transform 0.3s; transform: scale(1);">📦</div>
            <div style="font-size: 0.65rem; color: var(--green); text-transform: uppercase; font-weight: 800; margin-top: 5px; letter-spacing: 1px;">Chest Unlocked!</div>
        `;
    }

    let itemsListHtml = "";
    if (rewards.items) {
        Object.entries(rewards.items).forEach(([name, qty]) => {
            if (name.toLowerCase() === 'mystery chest' || name.toLowerCase() === 'mystery_chest') return;
            let emoji = "📦";
            if (name.toLowerCase() === 'crystals') emoji = "💎";
            else if (name.toLowerCase() in ['reward points', 'reward_points']) emoji = "⭐";
            else if (name.toLowerCase().includes('ball')) emoji = "🔴";
            
            itemsListHtml += `<div style="font-size: 0.95rem; font-weight: 700; color: #fff; margin-top: 4px;">${emoji} ${name} x${qty}</div>`;
        });
    }

    box.innerHTML = `
      <div class="reward-chest-glow">
        ${chestHtml}
      </div>
      <h2 class="reward-title-text" style="font-size: 2rem;">MISSION COMPLETED!</h2>
      
      <div style="margin: 15px 0;">
        <div style="font-size: 1.5rem; font-weight: 900; color: var(--yellow); text-shadow: 0 0 10px rgba(255,203,5,0.4);" id="popup-coin-counter">🪙 +0 Coins</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: var(--blue);" id="popup-xp-counter">🎫 +0 XP</div>
        
        <div style="width: 200px; height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; margin: 10px auto 0;">
            <div id="popup-xp-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--green), var(--blue)); transition: width 1.2s cubic-bezier(0.1, 0.8, 0.25, 1);"></div>
        </div>
      </div>
      
      <div id="popup-items-unlocked" style="margin-top: 12px; opacity: 0; transition: opacity 0.5s;">
        ${itemsListHtml}
      </div>
    `;
    
    overlay.classList.add("show");
    playRewardChimeSound();
    explodeRewardParticles();
    
    if (hasMysteryChest) {
        setTimeout(() => {
            const chestIcon = document.getElementById("chest-animation-icon");
            if (chestIcon) {
                chestIcon.style.transform = "scale(1.2) rotate(5deg)";
                try {
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.frequency.setValueAtTime(80, audioCtx.currentTime);
                    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.start();
                    osc.stop(audioCtx.currentTime + 0.5);
                } catch(e) {}
                
                setTimeout(() => {
                    chestIcon.textContent = "🔓";
                    chestIcon.style.transform = "scale(1) rotate(0deg)";
                }, 150);
            }
        }, 400);
    }
    
    const coinsTarget = rewards.amount || 0;
    const coinsEl = document.getElementById("popup-coin-counter");
    if (coinsEl && coinsTarget > 0) {
        let current = 0;
        const step = Math.ceil(coinsTarget / 30);
        const coinTimer = setInterval(() => {
            current = Math.min(coinsTarget, current + step);
            coinsEl.textContent = `🪙 +${current} Coins`;
            if (current === coinsTarget) clearInterval(coinTimer);
        }, 20);
    } else if (coinsEl) {
        coinsEl.style.display = "none";
    }
    
    const xpTarget = rewards.xp || 0;
    const xpEl = document.getElementById("popup-xp-counter");
    const xpBar = document.getElementById("popup-xp-bar");
    if (xpEl && xpTarget > 0) {
        let current = 0;
        const step = Math.ceil(xpTarget / 30);
        const xpTimer = setInterval(() => {
            current = Math.min(xpTarget, current + step);
            xpEl.textContent = `🎫 +${current} XP`;
            if (current === xpTarget) clearInterval(xpTimer);
        }, 20);
        
        setTimeout(() => {
            if (xpBar) xpBar.style.width = "100%";
        }, 150);
    } else if (xpEl) {
        xpEl.style.display = "none";
        if (xpBar) xpBar.parentNode.style.display = "none";
    }
    
    setTimeout(() => {
        const itemsDiv = document.getElementById("popup-items-unlocked");
        if (itemsDiv) itemsDiv.style.opacity = "1";
    }, 800);
    
    setTimeout(() => {
        overlay.classList.remove("show");
        showToast("Mission Completed! Rewards claimed successfully.");
    }, 3500);
}

// Sync function for rewards.html
async function syncRewardsDataFromBackend() {
    // 1. Fetch Dashboard Stats
    try {
        const dbStats = await syncApiRequest("/rewards/dashboard/");
        if (dbStats) {
            document.getElementById("stat-rewards-claimed").textContent = dbStats.total_collected_rewards;
            document.getElementById("stat-coins-earned").textContent = dbStats.total_coins_earned.toLocaleString();
            document.getElementById("stat-xp-earned").textContent = dbStats.total_xp_earned.toLocaleString();
            document.getElementById("stat-crystals").textContent = dbStats.total_crystals.toLocaleString();
            document.getElementById("stat-streak").textContent = `${dbStats.login_streak} / 30`;
            document.getElementById("stat-bp-level").textContent = `LV ${dbStats.battle_pass_level}`;
            document.getElementById("stat-reward-points").textContent = dbStats.reward_points.toLocaleString();
        }
    } catch (e) {
        console.error("Failed to load dashboard stats:", e);
    }

    // 2. Fetch Daily Login Calendar config
    try {
        const dailyData = await syncApiRequest("/rewards/daily/");
        if (dailyData) {
            const cooldownBadge = document.getElementById("daily-cooldown-badge");
            if (cooldownBadge) {
                if (dailyData.has_claimed_today) {
                    cooldownBadge.textContent = "Next Claim: " + formatTime(dailyData.cooldown_seconds);
                    cooldownBadge.className = "cooldown-badge";
                    if (window.dailyTimerInterval) clearInterval(window.dailyTimerInterval);
                    let remaining = dailyData.cooldown_seconds;
                    window.dailyTimerInterval = setInterval(() => {
                        remaining = Math.max(0, remaining - 1);
                        cooldownBadge.textContent = "Next Claim: " + formatTime(remaining);
                        if (remaining === 0) {
                            clearInterval(window.dailyTimerInterval);
                            cooldownBadge.textContent = "Ready to Claim";
                            cooldownBadge.className = "cooldown-badge ready";
                            const btn = document.getElementById("btn-claim-daily");
                            if (btn) btn.disabled = false;
                        }
                    }, 1000);
                } else {
                    cooldownBadge.textContent = "Ready to Claim";
                    cooldownBadge.className = "cooldown-badge ready";
                    const btn = document.getElementById("btn-claim-daily");
                    if (btn) btn.disabled = false;
                }
            }

            const grid = document.getElementById("daily-calendar-grid");
            if (grid) {
                grid.innerHTML = "";
                const itemIcons = {
                    "Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/potion.png",
                    "Super Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/super-potion.png",
                    "Hyper Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/hyper-potion.png",
                    "Max Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/max-potion.png",
                    "Poke Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png",
                    "Great Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/great-ball.png",
                    "Ultra Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/ultra-ball.png",
                    "Master Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png",
                    "Rare Candy": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/rare-candy.png"
                };

                dailyData.rewards.forEach(r => {
                    const card = document.createElement("div");
                    let statusClass = "locked";
                    if (r.claimed) statusClass = "claimed";
                    else if (r.claimable) statusClass = "claimable";
                    
                    card.className = `day-card ${statusClass}`;
                    
                    let iconHtml = "";
                    if (r.reward_type === "Coins") iconHtml = "🪙";
                    else if (r.reward_type === "Crystals") iconHtml = "💎";
                    else if (r.reward_type === "XP") iconHtml = "🎫";
                    else if (r.reward_type === "Item" && itemIcons[r.item_name]) {
                        iconHtml = `<img src="${itemIcons[r.item_name]}" alt="${r.item_name}" />`;
                    } else {
                        iconHtml = "🎁";
                    }

                    card.innerHTML = `
                        <div class="day-title">DAY ${r.day}</div>
                        <div class="day-icon">${iconHtml}</div>
                        <div class="day-val">${r.reward_type === 'Item' ? r.item_name : '+' + r.amount + ' ' + r.reward_type}</div>
                        <div class="claimed-overlay">Claimed ✓</div>
                    `;
                    grid.appendChild(card);
                });
            }
        }
    } catch (e) {
        console.error("Failed to load daily login calendar:", e);
    }

    // 3. Fetch Level Rewards milestones
    try {
        const lvlData = await syncApiRequest("/rewards/level/");
        if (lvlData) {
            const container = document.getElementById("level-milestones-container");
            if (container) {
                container.innerHTML = "";
                const itemIcons = {
                    "Potion": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/potion.png",
                    "Great Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/great-ball.png",
                    "Ultra Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/ultra-ball.png",
                    "Master Ball": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png",
                    "Rare Candy": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/rare-candy.png"
                };

                lvlData.milestones.forEach(m => {
                    const item = document.createElement("div");
                    item.className = `milestone-item ${m.claimable ? 'claimable' : ''}`;
                    
                    let subHtml = "";
                    if (m.reward_type === "Coins") subHtml = "🪙 +" + m.amount + " Coins";
                    else if (m.reward_type === "Crystals") subHtml = "💎 +" + m.amount + " Crystals";
                    else if (m.reward_type === "Item" && itemIcons[m.item_name]) {
                        subHtml = `<img src="${itemIcons[m.item_name]}" /> x${m.amount} ${m.item_name}`;
                    } else {
                        subHtml = "🎁 Reward";
                    }

                    let btnText = "Locked";
                    let btnClass = "";
                    if (m.claimed) {
                        btnText = "Claimed";
                        btnClass = "disabled";
                    } else if (m.claimable) {
                        btnText = "Claim";
                        btnClass = "claimable";
                    }

                    item.innerHTML = `
                        <div class="milestone-left">
                            <div class="level-badge"><span>LV</span><val>${m.level}</val></div>
                            <div class="milestone-info">
                                <div class="milestone-reward-desc">Milestone Rewards</div>
                                <div class="milestone-reward-sub">${subHtml}</div>
                            </div>
                        </div>
                        <button class="btn-milestone-claim ${btnClass}" ${btnText !== 'Claim' ? 'disabled' : ''} onclick="claimLevelMilestone(${m.level})">${btnText}</button>
                    `;
                    container.appendChild(item);
                });
            }
        }
    } catch (e) {
        console.error("Failed to load level rewards:", e);
    }

    // 4. Fetch Active Events
    try {
        const eventData = await syncApiRequest("/rewards/events/");
        if (eventData && Array.isArray(eventData)) {
            const container = document.getElementById("active-events-container");
            if (container) {
                container.innerHTML = "";
                eventData.forEach(ev => {
                    const card = document.createElement("div");
                    card.className = "event-card";
                    
                    let rewardText = "";
                    if (ev.reward_type === "Coins") rewardText = "🪙 " + ev.amount + " Coins";
                    else if (ev.reward_type === "Crystals") rewardText = "💎 " + ev.amount + " Crystals";
                    else rewardText = "🎁 " + ev.item_name + " x" + ev.amount;

                    card.innerHTML = `
                        <div class="event-header">
                            <div class="event-img"><img src="${ev.image}" /></div>
                            <div class="event-meta">
                                <h3 class="event-title">${ev.title}</h3>
                                <span class="event-type">${ev.event_type} Event</span>
                            </div>
                        </div>
                        <p class="event-desc">${ev.description}</p>
                        <div class="event-footer">
                            <div class="event-timer">⏳ ${formatTime(ev.cooldown_seconds)}</div>
                            <button class="btn-event-claim" ${ev.claimed ? 'disabled' : ''} onclick="claimEventReward(${ev.id})">${ev.claimed ? 'Claimed' : 'Claim'}</button>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        }
    } catch (e) {
        console.error("Failed to load active events:", e);
    }

    // 5. Fetch History Logs
    try {
        await syncHistoryLogs(1);
    } catch (e) {
        console.error("Failed to load history logs:", e);
    }
}

// Fetch history logs helper
async function syncHistoryLogs(page = 1) {
    try {
        const searchQuery = document.getElementById("history-search")?.value || "";
        const filterVal = document.getElementById("history-category-filter")?.value || "";
        const endpoint = `/rewards/history/?page=${page}&search=${searchQuery}&category=${filterVal}`;
        const data = await syncApiRequest(endpoint);
        if (data) {
            const tbody = document.getElementById("history-table-tbody");
            if (tbody) {
                tbody.innerHTML = "";

                if (!data.results || data.results.length === 0) {
                    tbody.innerHTML = "<tr><td colspan='4' style='text-align:center;color:rgba(255,255,255,0.3)'>No rewards claimed yet.</td></tr>";
                    document.getElementById("history-pagination-info").textContent = "Showing 0 to 0 of 0 logs";
                    document.getElementById("btn-history-prev").disabled = true;
                    document.getElementById("btn-history-next").disabled = true;
                    return;
                }

                data.results.forEach(log => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${log.reward}</td>
                        <td>+${log.amount}</td>
                        <td>${log.earned_from}</td>
                        <td style="font-size:0.75rem;color:rgba(255,255,255,0.4)">${log.date}</td>
                    `;
                    tbody.appendChild(tr);
                });

                const count = data.count || data.results.length;
                const start = (page - 1) * 8 + 1;
                const end = Math.min(page * 8, count);
                document.getElementById("history-pagination-info").textContent = `Showing ${start} to ${end} of ${count} logs`;
                
                const prevBtn = document.getElementById("btn-history-prev");
                const nextBtn = document.getElementById("btn-history-next");
                
                if (prevBtn) {
                    prevBtn.disabled = !data.previous;
                    prevBtn.onclick = () => syncHistoryLogs(page - 1);
                }
                if (nextBtn) {
                    nextBtn.disabled = !data.next;
                    nextBtn.onclick = () => syncHistoryLogs(page + 1);
                }
            }
        }
    } catch(e) {
        console.error("Failed to sync history log page:", e);
    }
}

function registerSyncHooks() {
    const href = window.location.href.toLowerCase();

    // 1. Hook pokedex.html
    if (href.includes("pokedex.html")) {
        console.log("Registering Pokédex hooks...");
        if (window.initPokedex) {
            const originalInit = window.initPokedex;
            window.initPokedex = async function() {
                await syncPokedexFromBackend();
                originalInit();
            };
        }
        if (window.addToTeam) {
            const originalAddToTeam = window.addToTeam;
            window.addToTeam = async function(pokemonName) {
                const success = originalAddToTeam(pokemonName);
                if (success) {
                    try {
                        const localPokedexStr = localStorage.getItem('pokemonNexus_pokedex_152');
                        let details = null;
                        if (localPokedexStr) {
                            try {
                                const localPokedex = JSON.parse(localPokedexStr);
                                details = localPokedex.find(x => x.name.toLowerCase() === pokemonName.toLowerCase());
                            } catch (e) {}
                        }
                        if (!details && window.pokemonList) {
                            details = window.pokemonList.find(x => x.name.toLowerCase() === pokemonName.toLowerCase());
                        }
                        if (details) {
                            const type1 = details.types && details.types[0] ? details.types[0] : "Normal";
                            const type2 = details.types && details.types[1] ? details.types[1] : null;
                            const hp = details.hp || 100;
                            const attack = details.attack || 80;
                            const defense = details.defense || 80;
                            const speed = details.speed || 80;
                            const special_attack = details.spAtk || 80;
                            const special_defense = details.spDef || 80;

                            const payload = {
                                pokedex_number: details.id,
                                name: details.name,
                                type1: type1,
                                type2: type2,
                                rarity: details.rarity || "Common",
                                level: Math.floor(Math.random() * 50) + 15,
                                hp: hp,
                                max_hp: hp,
                                attack: attack,
                                defense: defense,
                                speed: speed,
                                special_attack: special_attack,
                                special_defense: special_defense,
                                nature: "Hardy",
                                ability: details.abilities && details.abilities.length > 0 ? details.abilities[0] : "Overgrow",
                                moves: details.moves ? details.moves.slice(0, 4).map(m => ({name: m, type: type1, pp: "15/15"})) : [
                                    {name: "Tackle", type: "Normal", pp: "35/35"},
                                    {name: "Growl", type: "Normal", pp: "40/40"}
                                ],
                                image: details.artwork || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${details.id}.png`,
                                shiny: Math.random() < 0.05,
                                is_in_party: true
                            };
                            await syncApiRequest("/pokemon/", "POST", payload);
                        }
                    } catch (e) {
                        console.error("Failed to sync team member to backend:", e);
                    }
                }
            };
        }
    }

    // 2. Hook inventory.html
    if (href.includes("inventory.html")) {
        console.log("Registering Inventory hooks...");
        if (window.initInventory) {
            const originalInit = window.initInventory;
            window.initInventory = async function() {
                await syncInventoryFromBackend();
                originalInit();
            };
        }
        if (window.saveInventory) {
            const originalSave = window.saveInventory;
            window.saveInventory = async function() {
                originalSave();
                await syncInventoryToBackend(window.inventory);
            };
        }
    }

    // 3. Hook kingdom-map.html
    if (href.includes("kingdom-map.html")) {
        console.log("Registering Kingdom Map hooks...");
        if (window.initMapData) {
            const originalInit = window.initMapData;
            window.initMapData = async function() {
                await syncMapFromBackend();
                originalInit();
            };
        }
        if (window.saveMapData) {
            const originalSave = window.saveMapData;
            window.saveMapData = async function() {
                originalSave();
                await syncMapToBackend(window.dbRegions);
            };
        }
    }

    // 4. Hook battle.html
    if (href.includes("battle.html")) {
        console.log("Registering Battle Screen hooks...");
        if (window.renderTeamSidebar) {
            const originalRenderTeam = window.renderTeamSidebar;
            window.renderTeamSidebar = async function() {
                if (!window.battleSynced) {
                    window.battleSynced = true;
                    await syncBattleDataFromBackend();
                    if (window.renderBagSidebar) window.renderBagSidebar();
                    if (window.renderMovesGrid) window.renderMovesGrid();
                }
                originalRenderTeam();
            };
        }
    }

    // 5. Hook leaderboard.html
    if (href.includes("leaderboard.html")) {
        console.log("Registering Leaderboard hooks...");
        if (window.renderTable) {
            const originalRender = window.renderTable;
            window.renderTable = async function() {
                if (!window.leaderboardSynced) {
                    window.leaderboardSynced = true;
                    await syncLeaderboardFromBackend();
                }
                originalRender();
            };
        }
    }

    // 6. Hook profile.html
    if (href.includes("profile.html")) {
        console.log("Registering Profile hooks...");
        if (window.renderTrainerCard) {
            const originalRender = window.renderTrainerCard;
            window.renderTrainerCard = async function() {
                if (!window.profileSynced) {
                    window.profileSynced = true;
                    await syncProfileFromBackend();
                    await syncProfileRewardsSummary();
                }
                originalRender();
            };
        }
    }
}

// Safely execute hook registration considering readyState
if (document.readyState === "interactive" || document.readyState === "complete") {
    registerSyncHooks();
} else {
    window.addEventListener("DOMContentLoaded", registerSyncHooks);
}

window.addEventListener("DOMContentLoaded", () => {

    // --- ADMIN REWARDS MANAGEMENT CODE ---
    let currentHistoryPage = 1;
    let historySearchQuery = "";
    let historyFilterQuery = "";

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function escapeHtml(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    async function syncAdminRewardsData() {
        const section = document.getElementById("section-rewards");
        if (!section) return;
        
        try {
            const analytics = await syncApiRequest("/admin/rewards/analytics/");
            if (analytics) {
                document.getElementById("stat-total-claims").textContent = analytics.total_claims || 0;
                document.getElementById("stat-most-claimed").textContent = analytics.most_claimed || "None";
                document.getElementById("stat-coins-dist").textContent = `🪙 ${analytics.total_coins || 0}`;
                document.getElementById("stat-xp-dist").textContent = `🎫 ${analytics.total_xp || 0}`;
                document.getElementById("stat-crystals-dist").textContent = `✨ ${analytics.total_crystals || 0}`;
                document.getElementById("stat-daily-claims").textContent = analytics.daily_claims || 0;
                document.getElementById("stat-mission-claims").textContent = analytics.mission_claims || 0;
                document.getElementById("stat-battle-claims").textContent = analytics.battle_claims || 0;
                
                const auditTbody = document.getElementById("admin-audit-tbody");
                if (auditTbody) {
                    auditTbody.innerHTML = "";
                    const logs = analytics.change_logs || [];
                    if (logs.length === 0) {
                        auditTbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:rgba(255,255,255,0.3);">No audit logs recorded yet.</td></tr>`;
                    } else {
                        logs.forEach(log => {
                            const tr = document.createElement("tr");
                            tr.innerHTML = `
                                <td>${log.timestamp}</td>
                                <td>${escapeHtml(log.admin)}</td>
                                <td><strong>${escapeHtml(log.action)}</strong></td>
                                <td style="font-family:monospace; font-size:0.75rem; color:var(--text-gray);">${escapeHtml(log.details)}</td>
                            `;
                            auditTbody.appendChild(tr);
                        });
                    }
                }
            }
            
            const config = await syncApiRequest("/admin/rewards/config/");
            if (config) {
                window.adminRewardsConfig = config;
                renderAdminDailyRewards();
                renderAdminLevelRewards();
                renderAdminBattleRewards();
                renderAdminGeneralSettings();
            }
            
            const missions = await syncApiRequest("/admin/rewards/missions/");
            if (missions) {
                window.adminMissionsDb = missions;
                renderAdminMissions();
            }
            
            const events = await syncApiRequest("/admin/rewards/events/");
            if (events) {
                window.adminEventsDb = events;
                renderAdminEvents();
            }
            
            await syncAdminRewardHistory();
            
        } catch(e) {
            console.error("Failed to fetch admin rewards data:", e);
        }
    }

    function initRewardsAdminSubtabs() {
        const section = document.getElementById("section-rewards");
        if (!section) return;
        
        const subtabs = section.querySelectorAll(".btn-sub-tab");
        subtabs.forEach(btn => {
            const subtabId = btn.getAttribute("data-subtab");
            if (!subtabId) return;
            
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener("click", () => {
                newBtn.parentNode.querySelectorAll(".btn-sub-tab").forEach(b => b.classList.remove("active"));
                newBtn.classList.add("active");
                
                section.querySelectorAll(".subtab-content").forEach(content => {
                    content.style.display = "none";
                });
                
                const target = document.getElementById(`subtab-${subtabId}`);
                if (target) target.style.display = "block";
                
                if (subtabId === "history") {
                    syncAdminRewardHistory();
                }
            });
        });
    }

    function renderAdminDailyRewards() {
        const tbody = document.getElementById("admin-daily-tbody");
        if (!tbody || !window.adminRewardsConfig) return;
        
        tbody.innerHTML = "";
        const list = window.adminRewardsConfig.daily_rewards || [];
        list.forEach((item, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>Day ${item.day}</strong></td>
                <td><span class="difficulty-${item.type === 'Item' ? 'medium' : 'easy'}" style="text-transform:capitalize;">${item.type}</span></td>
                <td>${item.amount}</td>
                <td>${item.item_name || '<span style="color:rgba(255,255,255,0.25);">None</span>'}</td>
                <td>
                    <button class="btn-mission-edit" onclick="editDailyReward(${idx})">Edit</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    window.editDailyReward = function(index) {
        const item = window.adminRewardsConfig.daily_rewards[index];
        const html = `
            <div class="form-group">
                <label>Reward Type</label>
                <select id="edit-daily-type" onchange="toggleDailyItemField(this.value)">
                    <option value="Coins" ${item.type === 'Coins' ? 'selected' : ''}>Coins</option>
                    <option value="XP" ${item.type === 'XP' ? 'selected' : ''}>XP</option>
                    <option value="Crystals" ${item.type === 'Crystals' ? 'selected' : ''}>Crystals</option>
                    <option value="Item" ${item.type === 'Item' ? 'selected' : ''}>Inventory Item</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reward Amount / Quantity</label>
                <input type="number" id="edit-daily-amount" value="${item.amount}" min="1" required />
            </div>
            <div class="form-group" id="daily-item-name-group" style="${item.type === 'Item' ? '' : 'display:none;'}">
                <label>Reward Item Name</label>
                <select id="edit-daily-item-name">
                    <option value="Poke Ball" ${item.item_name === 'Poke Ball' ? 'selected' : ''}>Poke Ball</option>
                    <option value="Great Ball" ${item.item_name === 'Great Ball' ? 'selected' : ''}>Great Ball</option>
                    <option value="Ultra Ball" ${item.item_name === 'Ultra Ball' ? 'selected' : ''}>Ultra Ball</option>
                    <option value="Master Ball" ${item.item_name === 'Master Ball' ? 'selected' : ''}>Master Ball</option>
                    <option value="Potion" ${item.item_name === 'Potion' ? 'selected' : ''}>Potion</option>
                    <option value="Super Potion" ${item.item_name === 'Super Potion' ? 'selected' : ''}>Super Potion</option>
                    <option value="Hyper Potion" ${item.item_name === 'Hyper Potion' ? 'selected' : ''}>Hyper Potion</option>
                    <option value="Max Potion" ${item.item_name === 'Max Potion' ? 'selected' : ''}>Max Potion</option>
                    <option value="Rare Candy" ${item.item_name === 'Rare Candy' ? 'selected' : ''}>Rare Candy</option>
                    <option value="Fire Stone" ${item.item_name === 'Fire Stone' ? 'selected' : ''}>Fire Stone</option>
                    <option value="Water Stone" ${item.item_name === 'Water Stone' ? 'selected' : ''}>Water Stone</option>
                    <option value="Thunder Stone" ${item.item_name === 'Thunder Stone' ? 'selected' : ''}>Thunder Stone</option>
                    <option value="Leaf Stone" ${item.item_name === 'Leaf Stone' ? 'selected' : ''}>Leaf Stone</option>
                </select>
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal(`📅 Edit Day ${item.day} Daily Reward`, html, async () => {
                const type = document.getElementById("edit-daily-type").value;
                const amount = parseInt(document.getElementById("edit-daily-amount").value);
                const item_name = type === 'Item' ? document.getElementById("edit-daily-item-name").value : null;
                
                if (isNaN(amount) || amount <= 0) {
                    showToast("Amount must be a positive integer!");
                    return;
                }
                
                window.adminRewardsConfig.daily_rewards[index] = {
                    day: item.day,
                    type,
                    amount,
                    item_name
                };
                
                try {
                    await syncApiRequest("/admin/rewards/config/", "POST", { daily_rewards: window.adminRewardsConfig.daily_rewards });
                    showToast("Daily rewards schedule updated!");
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to save changes: " + e.message);
                }
            });
        }
    };

    window.toggleDailyItemField = function(val) {
        const group = document.getElementById("daily-item-name-group");
        if (group) group.style.display = val === 'Item' ? 'block' : 'none';
    };

    function renderAdminLevelRewards() {
        const tbody = document.getElementById("admin-level-tbody");
        if (!tbody || !window.adminRewardsConfig) return;
        
        tbody.innerHTML = "";
        const list = window.adminRewardsConfig.level_rewards || [];
        list.forEach((item, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>Level ${item.level}</strong></td>
                <td><span class="difficulty-${item.type === 'Item' ? 'medium' : 'easy'}" style="text-transform:capitalize;">${item.type}</span></td>
                <td>${item.amount}</td>
                <td>${item.item_name || '<span style="color:rgba(255,255,255,0.25);">None</span>'}</td>
                <td>
                    <div style="display:flex; gap:6px;">
                        <button class="btn-mission-edit" onclick="editLevelReward(${idx})">Edit</button>
                        <button class="btn-mission-delete" onclick="deleteLevelReward(${idx})">Delete</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        const addBtn = document.getElementById("admin-level-add-btn");
        if (addBtn) {
            addBtn.onclick = () => openAddLevelRewardModal();
        }
    }

    window.openAddLevelRewardModal = function() {
        const html = `
            <div class="form-group">
                <label>Target Level Milestone</label>
                <input type="number" id="add-level-milestone" min="1" required />
            </div>
            <div class="form-group">
                <label>Reward Type</label>
                <select id="add-level-type" onchange="toggleLevelItemField(this.value)">
                    <option value="Coins">Coins</option>
                    <option value="XP">XP</option>
                    <option value="Crystals">Crystals</option>
                    <option value="Item">Inventory Item</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reward Amount</label>
                <input type="number" id="add-level-amount" min="1" required />
            </div>
            <div class="form-group" id="level-item-name-group" style="display:none;">
                <label>Reward Item Name</label>
                <select id="add-level-item-name">
                    <option value="Poke Ball">Poke Ball</option>
                    <option value="Great Ball">Great Ball</option>
                    <option value="Ultra Ball">Ultra Ball</option>
                    <option value="Master Ball">Master Ball</option>
                    <option value="Potion">Potion</option>
                    <option value="Super Potion">Super Potion</option>
                    <option value="Hyper Potion">Hyper Potion</option>
                    <option value="Max Potion">Max Potion</option>
                    <option value="Rare Candy">Rare Candy</option>
                    <option value="Fire Stone">Fire Stone</option>
                </select>
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal("🏆 Add Level Milestone Reward", html, async () => {
                const level = parseInt(document.getElementById("add-level-milestone").value);
                const type = document.getElementById("add-level-type").value;
                const amount = parseInt(document.getElementById("add-level-amount").value);
                const item_name = type === 'Item' ? document.getElementById("add-level-item-name").value : null;
                
                if (isNaN(level) || level <= 0 || isNaN(amount) || amount <= 0) {
                    showToast("Level and Amount must be positive integers!");
                    return;
                }
                
                const list = window.adminRewardsConfig.level_rewards || [];
                if (list.some(item => item.level === level)) {
                    showToast(`A reward is already configured for Level ${level}!`);
                    return;
                }
                
                list.push({ level, type, amount, item_name });
                list.sort((a, b) => a.level - b.level);
                
                try {
                    await syncApiRequest("/admin/rewards/config/", "POST", { level_rewards: list });
                    showToast(`Level ${level} milestone reward added!`);
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to add milestone: " + e.message);
                }
            });
        }
    };

    window.editLevelReward = function(idx) {
        const item = window.adminRewardsConfig.level_rewards[idx];
        const html = `
            <div class="form-group">
                <label>Reward Type</label>
                <select id="edit-level-type" onchange="toggleLevelItemField(this.value)">
                    <option value="Coins" ${item.type === 'Coins' ? 'selected' : ''}>Coins</option>
                    <option value="XP" ${item.type === 'XP' ? 'selected' : ''}>XP</option>
                    <option value="Crystals" ${item.type === 'Crystals' ? 'selected' : ''}>Crystals</option>
                    <option value="Item" ${item.type === 'Item' ? 'selected' : ''}>Inventory Item</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reward Amount</label>
                <input type="number" id="edit-level-amount" value="${item.amount}" min="1" required />
            </div>
            <div class="form-group" id="level-item-name-group" style="${item.type === 'Item' ? '' : 'display:none;'}">
                <label>Reward Item Name</label>
                <select id="edit-level-item-name">
                    <option value="Poke Ball" ${item.item_name === 'Poke Ball' ? 'selected' : ''}>Poke Ball</option>
                    <option value="Great Ball" ${item.item_name === 'Great Ball' ? 'selected' : ''}>Great Ball</option>
                    <option value="Ultra Ball" ${item.item_name === 'Ultra Ball' ? 'selected' : ''}>Ultra Ball</option>
                    <option value="Master Ball" ${item.item_name === 'Master Ball' ? 'selected' : ''}>Master Ball</option>
                    <option value="Potion" ${item.item_name === 'Potion' ? 'selected' : ''}>Potion</option>
                    <option value="Super Potion" ${item.item_name === 'Super Potion' ? 'selected' : ''}>Super Potion</option>
                    <option value="Hyper Potion" ${item.item_name === 'Hyper Potion' ? 'selected' : ''}>Hyper Potion</option>
                    <option value="Max Potion" ${item.item_name === 'Max Potion' ? 'selected' : ''}>Max Potion</option>
                    <option value="Rare Candy" ${item.item_name === 'Rare Candy' ? 'selected' : ''}>Rare Candy</option>
                    <option value="Fire Stone" ${item.item_name === 'Fire Stone' ? 'selected' : ''}>Fire Stone</option>
                </select>
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal(`🏆 Edit Level ${item.level} Reward`, html, async () => {
                const type = document.getElementById("edit-level-type").value;
                const amount = parseInt(document.getElementById("edit-level-amount").value);
                const item_name = type === 'Item' ? document.getElementById("edit-level-item-name").value : null;
                
                if (isNaN(amount) || amount <= 0) {
                    showToast("Amount must be a positive integer!");
                    return;
                }
                
                window.adminRewardsConfig.level_rewards[idx] = {
                    level: item.level,
                    type,
                    amount,
                    item_name
                };
                
                try {
                    await syncApiRequest("/admin/rewards/config/", "POST", { level_rewards: window.adminRewardsConfig.level_rewards });
                    showToast(`Level ${item.level} reward updated!`);
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to save changes: " + e.message);
                }
            });
        }
    };

    window.deleteLevelReward = function(idx) {
        const item = window.adminRewardsConfig.level_rewards[idx];
        if (!confirm(`Are you sure you want to delete the Level ${item.level} milestone reward?`)) return;
        
        window.adminRewardsConfig.level_rewards.splice(idx, 1);
        
        syncApiRequest("/admin/rewards/config/", "POST", { level_rewards: window.adminRewardsConfig.level_rewards })
            .then(() => {
                showToast(`Deleted Level ${item.level} milestone reward.`);
                syncAdminRewardsData();
            })
            .catch(e => showToast("Failed to delete milestone: " + e.message));
    };

    window.toggleLevelItemField = function(val) {
        const group = document.getElementById("level-item-name-group");
        if (group) group.style.display = val === 'Item' ? 'block' : 'none';
    };

    function renderAdminMissions() {
        const tbody = document.getElementById("admin-mission-tbody");
        if (!tbody || !window.adminMissionsDb) return;
        
        tbody.innerHTML = "";
        window.adminMissionsDb.forEach((m, idx) => {
            let itemsDesc = "";
            if (m.reward_items) {
                itemsDesc = Object.entries(m.reward_items).map(([name, qty]) => `${name} x${qty}`).join(", ");
            }
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(m.title)}</strong></td>
                <td><span class="difficulty-${m.type === 'story' ? 'hard' : (m.type === 'weekly' ? 'medium' : 'easy')}" style="text-transform:capitalize;">${m.type}</span></td>
                <td>${m.required_progress}</td>
                <td>🎫 ${m.reward_xp}</td>
                <td>🪙 ${m.reward_coins}</td>
                <td>${itemsDesc || '<span style="color:rgba(255,255,255,0.25);">None</span>'}</td>
                <td>
                    <div style="display:flex; gap:6px;">
                        <button class="btn-mission-edit" onclick="editAdminMission(${m.id})">Edit</button>
                        <button class="btn-mission-delete" onclick="deleteAdminMission(${m.id})">Delete</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        const addBtn = document.getElementById("admin-mission-add-btn");
        if (addBtn) {
            addBtn.onclick = () => openAddAdminMissionModal();
        }
    }

    window.openAddAdminMissionModal = function() {
        const html = `
            <div class="form-group">
                <label>Mission Title</label>
                <input type="text" id="add-mission-title" placeholder="e.g. Master Catcher" required />
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="add-mission-desc" placeholder="e.g. Catch 5 Pokémon in the wild" required />
            </div>
            <div class="form-group">
                <label>Mission Type</label>
                <select id="add-mission-type">
                    <option value="daily">Daily Mission</option>
                    <option value="weekly">Weekly Mission</option>
                    <option value="story">Story Mission</option>
                    <option value="special">Special Event Mission</option>
                </select>
            </div>
            <div class="form-group">
                <label>Target Progress Goal (Count)</label>
                <input type="number" id="add-mission-goal" value="1" min="1" required />
            </div>
            <div class="form-group" style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div>
                    <label>XP Reward</label>
                    <input type="number" id="add-mission-xp" value="100" min="0" required />
                </div>
                <div>
                    <label>Coins Reward</label>
                    <input type="number" id="add-mission-coins" value="100" min="0" required />
                </div>
            </div>
            <div class="form-group">
                <label>Reward Item</label>
                <select id="add-mission-reward-item">
                    <option value="">None</option>
                    <option value="Poke Ball">Poke Ball</option>
                    <option value="Great Ball">Great Ball</option>
                    <option value="Ultra Ball">Ultra Ball</option>
                    <option value="Master Ball">Master Ball</option>
                    <option value="Potion">Potion</option>
                    <option value="Rare Candy">Rare Candy</option>
                    <option value="Crystals">Crystals (10)</option>
                    <option value="Reward Points">Reward Points (50)</option>
                    <option value="Mystery Chest">Mystery Chest (1)</option>
                </select>
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal("🎯 Add New Quest Mission", html, async () => {
                const title = document.getElementById("add-mission-title").value.trim();
                const description = document.getElementById("add-mission-desc").value.trim();
                const type = document.getElementById("add-mission-type").value;
                const required_progress = parseInt(document.getElementById("add-mission-goal").value);
                const reward_xp = parseInt(document.getElementById("add-mission-xp").value);
                const reward_coins = parseInt(document.getElementById("add-mission-coins").value);
                const selectedItem = document.getElementById("add-mission-reward-item").value;
                
                if (!title || !description || isNaN(required_progress) || required_progress <= 0 || isNaN(reward_xp) || reward_xp < 0 || isNaN(reward_coins) || reward_coins < 0) {
                    showToast("Invalid inputs: check titles, progress goals, XP, and Coins!");
                    return;
                }
                
                const reward_items = {};
                if (selectedItem) {
                    if (selectedItem === "Crystals") reward_items["Crystals"] = 10;
                    else if (selectedItem === "Reward Points") reward_items["Reward Points"] = 50;
                    else reward_items[selectedItem] = 1;
                }
                
                const payload = {
                    title,
                    description,
                    type,
                    required_progress,
                    reward_xp,
                    reward_coins,
                    reward_items
                };
                
                try {
                    await syncApiRequest("/admin/rewards/missions/", "POST", payload);
                    showToast(`Mission "${title}" created successfully!`);
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to create mission: " + e.message);
                }
            });
        }
    };

    window.editAdminMission = function(missionId) {
        const m = window.adminMissionsDb.find(item => item.id === missionId);
        if (!m) return;
        
        let currentItem = "";
        if (m.reward_items) {
            currentItem = Object.keys(m.reward_items)[0] || "";
        }
        
        const html = `
            <div class="form-group">
                <label>Mission Title</label>
                <input type="text" id="edit-mission-title" value="${escapeHtml(m.title)}" required />
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="edit-mission-desc" value="${escapeHtml(m.description)}" required />
            </div>
            <div class="form-group">
                <label>Mission Type</label>
                <select id="edit-mission-type">
                    <option value="daily" ${m.type === 'daily' ? 'selected' : ''}>Daily Mission</option>
                    <option value="weekly" ${m.type === 'weekly' ? 'selected' : ''}>Weekly Mission</option>
                    <option value="story" ${m.type === 'story' ? 'selected' : ''}>Story Mission</option>
                    <option value="special" ${m.type === 'special' ? 'selected' : ''}>Special Event Mission</option>
                </select>
            </div>
            <div class="form-group">
                <label>Target Progress Goal (Count)</label>
                <input type="number" id="edit-mission-goal" value="${m.required_progress}" min="1" required />
            </div>
            <div class="form-group" style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div>
                    <label>XP Reward</label>
                    <input type="number" id="edit-mission-xp" value="${m.reward_xp}" min="0" required />
                </div>
                <div>
                    <label>Coins Reward</label>
                    <input type="number" id="edit-mission-coins" value="${m.reward_coins}" min="0" required />
                </div>
            </div>
            <div class="form-group">
                <label>Reward Item</label>
                <select id="edit-mission-reward-item">
                    <option value="" ${currentItem === '' ? 'selected' : ''}>None</option>
                    <option value="Poke Ball" ${currentItem === 'Poke Ball' ? 'selected' : ''}>Poke Ball</option>
                    <option value="Great Ball" ${currentItem === 'Great Ball' ? 'selected' : ''}>Great Ball</option>
                    <option value="Ultra Ball" ${currentItem === 'Ultra Ball' ? 'selected' : ''}>Ultra Ball</option>
                    <option value="Master Ball" ${currentItem === 'Master Ball' ? 'selected' : ''}>Master Ball</option>
                    <option value="Potion" ${currentItem === 'Potion' ? 'selected' : ''}>Potion</option>
                    <option value="Rare Candy" ${currentItem === 'Rare Candy' ? 'selected' : ''}>Rare Candy</option>
                    <option value="Crystals" ${currentItem === 'Crystals' ? 'selected' : ''}>Crystals (10)</option>
                    <option value="Reward Points" ${currentItem === 'Reward Points' ? 'selected' : ''}>Reward Points (50)</option>
                    <option value="Mystery Chest" ${currentItem === 'Mystery Chest' ? 'selected' : ''}>Mystery Chest (1)</option>
                </select>
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal(`🎯 Edit Mission: ${escapeHtml(m.title)}`, html, async () => {
                const title = document.getElementById("edit-mission-title").value.trim();
                const description = document.getElementById("edit-mission-desc").value.trim();
                const type = document.getElementById("edit-mission-type").value;
                const required_progress = parseInt(document.getElementById("edit-mission-goal").value);
                const reward_xp = parseInt(document.getElementById("edit-mission-xp").value);
                const reward_coins = parseInt(document.getElementById("edit-mission-coins").value);
                const selectedItem = document.getElementById("edit-mission-reward-item").value;
                
                if (!title || !description || isNaN(required_progress) || required_progress <= 0 || isNaN(reward_xp) || reward_xp < 0 || isNaN(reward_coins) || reward_coins < 0) {
                    showToast("Invalid inputs: check titles, progress goals, XP, and Coins!");
                    return;
                }
                
                const reward_items = {};
                if (selectedItem) {
                    if (selectedItem === "Crystals") reward_items["Crystals"] = 10;
                    else if (selectedItem === "Reward Points") reward_items["Reward Points"] = 50;
                    else reward_items[selectedItem] = 1;
                }
                
                const payload = {
                    title,
                    description,
                    type,
                    required_progress,
                    reward_xp,
                    reward_coins,
                    reward_items
                };
                
                try {
                    await syncApiRequest(`/admin/rewards/missions/${missionId}/`, "PATCH", payload);
                    showToast(`Mission updated successfully!`);
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to edit mission: " + e.message);
                }
            });
        }
    };

    window.deleteAdminMission = function(missionId) {
        const m = window.adminMissionsDb.find(item => item.id === missionId);
        if (!m) return;
        if (!confirm(`Are you sure you want to delete the mission: "${m.title}"?`)) return;
        
        syncApiRequest(`/admin/rewards/missions/${missionId}/`, "DELETE")
            .then(() => {
                showToast(`Deleted mission "${m.title}".`);
                syncAdminRewardsData();
            })
            .catch(e => showToast("Failed to delete mission: " + e.message));
    };

    function renderAdminBattleRewards() {
        if (!window.adminRewardsConfig || !window.adminRewardsConfig.battle_rewards) return;
        const br = window.adminRewardsConfig.battle_rewards;
        
        document.getElementById("battle-win-xp").value = br.win_xp || 0;
        document.getElementById("battle-win-coins").value = br.win_coins || 0;
        document.getElementById("battle-win-points").value = br.win_points || 0;
        document.getElementById("battle-item-chance").value = br.item_chance || 0;
        
        const container = document.getElementById("battle-item-weights-container");
        if (container) {
            container.innerHTML = "";
            const weights = br.item_weights || [];
            weights.forEach((w, idx) => {
                const div = document.createElement("div");
                div.className = "form-group";
                div.innerHTML = `
                    <label>${escapeHtml(w.name)} Weight</label>
                    <input type="number" class="battle-weight-input" data-item="${escapeHtml(w.name)}" value="${w.weight}" min="0" required style="width:100%; box-sizing:border-box;" />
                `;
                container.appendChild(div);
            });
        }
    }

    window.saveBattleRatesConfig = async function() {
        if (!window.adminRewardsConfig) return;
        
        const win_xp = parseInt(document.getElementById("battle-win-xp").value);
        const win_coins = parseInt(document.getElementById("battle-win-coins").value);
        const win_points = parseInt(document.getElementById("battle-win-points").value);
        const item_chance = parseFloat(document.getElementById("battle-item-chance").value);
        
        if (isNaN(win_xp) || win_xp < 0 || isNaN(win_coins) || win_coins < 0 || isNaN(win_points) || win_points < 0 || isNaN(item_chance) || item_chance < 0 || item_chance > 1) {
            showToast("Invalid inputs: check XP, coins, points, or item chance range!");
            return;
        }
        
        const item_weights = [];
        const inputs = document.querySelectorAll(".battle-weight-input");
        inputs.forEach(input => {
            const name = input.getAttribute("data-item");
            const weight = parseInt(input.value);
            item_weights.push({ name, weight: isNaN(weight) ? 0 : weight });
        });
        
        window.adminRewardsConfig.battle_rewards = {
            win_xp,
            win_coins,
            win_points,
            item_chance,
            item_weights
        };
        
        try {
            await syncApiRequest("/admin/rewards/config/", "POST", { battle_rewards: window.adminRewardsConfig.battle_rewards });
            showToast("Battle victory drop rates saved successfully!");
            await syncAdminRewardsData();
        } catch(e) {
            showToast("Failed to save battle drop rates: " + e.message);
        }
    };

    function renderAdminEvents() {
        const tbody = document.getElementById("admin-event-tbody");
        if (!tbody || !window.adminEventsDb) return;
        
        tbody.innerHTML = "";
        window.adminEventsDb.forEach((ev, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(ev.title)}</strong></td>
                <td>${escapeHtml(ev.description)}</td>
                <td>${ev.item_name ? `${escapeHtml(ev.item_name)}` : `<span class="difficulty-easy">${ev.reward_type}</span>`}</td>
                <td>${ev.amount}</td>
                <td>${ev.expires_at}</td>
                <td>
                    <div style="display:flex; gap:6px;">
                        <button class="btn-mission-edit" onclick="editAdminEvent(${ev.id})">Edit</button>
                        <button class="btn-mission-delete" onclick="deleteAdminEvent(${ev.id})">Delete</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        const addBtn = document.getElementById("admin-event-add-btn");
        if (addBtn) {
            addBtn.onclick = () => openAddAdminEventModal();
        }
    }

    window.openAddAdminEventModal = function() {
        const html = `
            <div class="form-group">
                <label>Event Title</label>
                <input type="text" id="add-event-title" placeholder="e.g. Summer Festival Boost" required />
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="add-event-desc" placeholder="e.g. Double XP event" required />
            </div>
            <div class="form-group">
                <label>Reward Type</label>
                <select id="add-event-reward-type" onchange="toggleEventItemField(this.value)">
                    <option value="Coins">Coins</option>
                    <option value="XP">XP</option>
                    <option value="Crystals">Crystals</option>
                    <option value="Item">Inventory Item</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reward Amount</label>
                <input type="number" id="add-event-amount" value="100" min="1" required />
            </div>
            <div class="form-group" id="event-item-name-group" style="display:none;">
                <label>Reward Item Name</label>
                <select id="add-event-item-name">
                    <option value="Poke Ball">Poke Ball</option>
                    <option value="Great Ball">Great Ball</option>
                    <option value="Ultra Ball">Ultra Ball</option>
                    <option value="Master Ball">Master Ball</option>
                    <option value="Potion">Potion</option>
                    <option value="Rare Candy">Rare Candy</option>
                </select>
            </div>
            <div class="form-group">
                <label>Expiration Date & Time</label>
                <input type="datetime-local" id="add-event-expires" required />
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal("🔥 Add Live Promo Event", html, async () => {
                const title = document.getElementById("add-event-title").value.trim();
                const description = document.getElementById("add-event-desc").value.trim();
                const reward_type = document.getElementById("add-event-reward-type").value;
                const amount = parseInt(document.getElementById("add-event-amount").value);
                const item_name = reward_type === 'Item' ? document.getElementById("add-event-item-name").value : null;
                const expires_at = document.getElementById("add-event-expires").value;
                
                if (!title || !description || isNaN(amount) || amount <= 0 || !expires_at) {
                    showToast("Invalid inputs: check titles, amounts, or expiration dates!");
                    return;
                }
                
                const payload = {
                    title,
                    description,
                    event_type: "limited",
                    reward_type,
                    amount,
                    item_name,
                    expires_at
                };
                
                try {
                    await syncApiRequest("/admin/rewards/events/", "POST", payload);
                    showToast(`Event "${title}" created successfully!`);
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to create event: " + e.message);
                }
            });
        }
    };

    window.editAdminEvent = function(eventId) {
        const ev = window.adminEventsDb.find(item => item.id === eventId);
        if (!ev) return;
        
        const html = `
            <div class="form-group">
                <label>Event Title</label>
                <input type="text" id="edit-event-title" value="${escapeHtml(ev.title)}" required />
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="edit-event-desc" value="${escapeHtml(ev.description)}" required />
            </div>
            <div class="form-group">
                <label>Reward Type</label>
                <select id="edit-event-reward-type" onchange="toggleEventItemField(this.value)">
                    <option value="Coins" ${ev.reward_type === 'Coins' ? 'selected' : ''}>Coins</option>
                    <option value="XP" ${ev.reward_type === 'XP' ? 'selected' : ''}>XP</option>
                    <option value="Crystals" ${ev.reward_type === 'Crystals' ? 'selected' : ''}>Crystals</option>
                    <option value="Item" ${ev.reward_type === 'Item' ? 'selected' : ''}>Inventory Item</option>
                </select>
            </div>
            <div class="form-group">
                <label>Reward Amount</label>
                <input type="number" id="edit-event-amount" value="${ev.amount}" min="1" required />
            </div>
            <div class="form-group" id="event-item-name-group" style="${ev.reward_type === 'Item' ? '' : 'display:none;'}">
                <label>Reward Item Name</label>
                <select id="edit-event-item-name">
                    <option value="Poke Ball" ${ev.item_name === 'Poke Ball' ? 'selected' : ''}>Poke Ball</option>
                    <option value="Great Ball" ${ev.item_name === 'Great Ball' ? 'selected' : ''}>Great Ball</option>
                    <option value="Ultra Ball" ${ev.item_name === 'Ultra Ball' ? 'selected' : ''}>Ultra Ball</option>
                    <option value="Master Ball" ${ev.item_name === 'Master Ball' ? 'selected' : ''}>Master Ball</option>
                    <option value="Potion" ${ev.item_name === 'Potion' ? 'selected' : ''}>Potion</option>
                    <option value="Rare Candy" ${ev.item_name === 'Rare Candy' ? 'selected' : ''}>Rare Candy</option>
                </select>
            </div>
            <div class="form-group">
                <label>Expiration Date & Time</label>
                <input type="datetime-local" id="edit-event-expires" value="${ev.expires_at}" required />
            </div>
        `;
        
        if (window.openCustomModal) {
            window.openCustomModal(`🔥 Edit Event: ${escapeHtml(ev.title)}`, html, async () => {
                const title = document.getElementById("edit-event-title").value.trim();
                const description = document.getElementById("edit-event-desc").value.trim();
                const reward_type = document.getElementById("edit-event-reward-type").value;
                const amount = parseInt(document.getElementById("edit-event-amount").value);
                const item_name = reward_type === 'Item' ? document.getElementById("edit-event-item-name").value : null;
                const expires_at = document.getElementById("edit-event-expires").value;
                
                if (!title || !description || isNaN(amount) || amount <= 0 || !expires_at) {
                    showToast("Invalid inputs: check titles, amounts, or expiration dates!");
                    return;
                }
                
                const payload = {
                    id: eventId,
                    title,
                    description,
                    reward_type,
                    amount,
                    item_name,
                    expires_at
                };
                
                try {
                    await syncApiRequest("/admin/rewards/events/", "PUT", payload);
                    showToast(`Event updated successfully!`);
                    await syncAdminRewardsData();
                } catch(e) {
                    showToast("Failed to edit event: " + e.message);
                }
            });
        }
    };

    window.deleteAdminEvent = function(eventId) {
        const ev = window.adminEventsDb.find(item => item.id === eventId);
        if (!ev) return;
        if (!confirm(`Are you sure you want to delete live event: "${ev.title}"?`)) return;
        
        syncApiRequest(`/admin/rewards/events/?id=${eventId}`, "DELETE")
            .then(() => {
                showToast(`Deleted event "${ev.title}".`);
                syncAdminRewardsData();
            })
            .catch(e => showToast("Failed to delete event: " + e.message));
    };

    window.toggleEventItemField = function(val) {
        const group = document.getElementById("event-item-name-group");
        if (group) group.style.display = val === 'Item' ? 'block' : 'none';
    };

    async function syncAdminRewardHistory() {
        const tbody = document.getElementById("admin-history-tbody");
        if (!tbody) return;
        
        let url = `/admin/rewards/history/?page=${currentHistoryPage}`;
        if (historySearchQuery) url += `&search=${encodeURIComponent(historySearchQuery)}`;
        if (historyFilterQuery) url += `&category=${encodeURIComponent(historyFilterQuery)}`;
        
        try {
            const res = await syncApiRequest(url);
            tbody.innerHTML = "";
            
            const results = res.results || [];
            if (results.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:rgba(255,255,255,0.3);">No rewards history matched.</td></tr>`;
                document.getElementById("history-page-info").textContent = "Page 1 of 1";
                return;
            }
            
            results.forEach(log => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${log.date}</td>
                    <td><strong>${escapeHtml(log.trainer)}</strong></td>
                    <td><span class="difficulty-${log.category === 'Item' ? 'medium' : 'easy'}">${escapeHtml(log.reward)}</span></td>
                    <td>${escapeHtml(log.earned_from)}</td>
                    <td><span class="status-badge status-active">${log.status}</span></td>
                `;
                tbody.appendChild(tr);
            });
            
            const totalCount = res.count || 0;
            const totalPages = Math.ceil(totalCount / 10) || 1;
            document.getElementById("history-page-info").textContent = `Page ${currentHistoryPage} of ${totalPages} (${totalCount} logs)`;
            
            document.getElementById("btn-admin-history-prev").disabled = (currentHistoryPage <= 1);
            document.getElementById("btn-admin-history-next").disabled = (currentHistoryPage >= totalPages);
            
        } catch(e) {
            console.error("Failed to load admin history:", e);
        }
    }

    function initHistoryLogControls() {
        const search = document.getElementById("admin-history-search");
        const filter = document.getElementById("admin-history-filter");
        
        if (search) {
            const newSearch = search.cloneNode(true);
            search.parentNode.replaceChild(newSearch, search);
            newSearch.addEventListener("input", debounce(() => {
                historySearchQuery = newSearch.value.trim();
                currentHistoryPage = 1;
                syncAdminRewardHistory();
            }, 300));
        }
        
        if (filter) {
            const newFilter = filter.cloneNode(true);
            filter.parentNode.replaceChild(newFilter, filter);
            newFilter.addEventListener("change", () => {
                historyFilterQuery = newFilter.value;
                currentHistoryPage = 1;
                syncAdminRewardHistory();
            });
        }
        
        const prev = document.getElementById("btn-admin-history-prev");
        const next = document.getElementById("btn-admin-history-next");
        if (prev && next) {
            prev.onclick = () => {
                if (currentHistoryPage > 1) {
                    currentHistoryPage--;
                    syncAdminRewardHistory();
                }
            };
            next.onclick = () => {
                currentHistoryPage++;
                syncAdminRewardHistory();
            };
        }
    }

    window.exportHistoryData = async function(format) {
        let url = `/admin/rewards/history/`;
        if (historySearchQuery) url += `?search=${encodeURIComponent(historySearchQuery)}`;
        if (historyFilterQuery) {
            url += (url.includes("?") ? "&" : "?") + `category=${encodeURIComponent(historyFilterQuery)}`;
        }
        
        try {
            const res = await syncApiRequest(url);
            const logs = res.results || res;
            
            let csvContent = "data:text/csv;charset=utf-8,";
            csvContent += "ID,Trainer,Reward,Earned From,Date,Status\n";
            
            logs.forEach(log => {
                const row = [
                    log.id,
                    `"${log.trainer}"`,
                    `"${log.reward}"`,
                    `"${log.earned_from}"`,
                    `"${log.date}"`,
                    `"${log.status}"`
                ].join(",");
                csvContent += row + "\n";
            });
            
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `reward_history.${format === 'excel' ? 'xlsx' : 'csv'}`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast(`Exported history to ${format.toUpperCase()} successfully!`);
        } catch(e) {
            showToast("Failed to export history: " + e.message);
        }
    };

    function renderAdminGeneralSettings() {
        if (!window.adminRewardsConfig || !window.adminRewardsConfig.settings) return;
        const s = window.adminRewardsConfig.settings;
        
        document.getElementById("streak-multiplier-toggle").checked = !!s.streak_multiplier_enabled;
        document.getElementById("weekend-xp-boost-toggle").checked = !!s.weekend_xp_boost_enabled;
    }

    window.saveGeneralSettings = async function() {
        if (!window.adminRewardsConfig) return;
        
        const streak_multiplier_enabled = document.getElementById("streak-multiplier-toggle").checked;
        const weekend_xp_boost_enabled = document.getElementById("weekend-xp-boost-toggle").checked;
        
        window.adminRewardsConfig.settings = {
            streak_multiplier_enabled,
            weekend_xp_boost_enabled
        };
        
        try {
            await syncApiRequest("/admin/rewards/config/", "POST", { settings: window.adminRewardsConfig.settings });
            showToast("General reward settings saved successfully!");
            await syncAdminRewardsData();
        } catch(e) {
            showToast("Failed to save settings: " + e.message);
        }
    };

    // 7. Hook admin/admin.html
    if (window.location.pathname.endsWith("admin.html")) {
        console.log("Registering Admin Dashboard hooks...");
        registerAdminInterceptors();
        if (window.refreshSectionContent) {
            const originalRefresh = window.refreshSectionContent;
            window.refreshSectionContent = async function(sectionId) {
                if (!window.adminDataSynced) {
                    window.adminDataSynced = true;
                    await syncAdminDataFromBackend();
                }
                
                if (sectionId === "rewards") {
                    initRewardsAdminSubtabs();
                    initHistoryLogControls();
                    await syncAdminRewardsData();
                }
                
                originalRefresh(sectionId);
            };
        }
    }

    // 8. Hook rewards.html
    if (window.location.pathname.endsWith("rewards.html")) {
        console.log("Registering Rewards hooks...");
        window.rewardsSynced = true;
        
        injectRewardsStyles();
        
        if (window.initRewardsPage) {
            const originalInit = window.initRewardsPage;
            window.initRewardsPage = async function() {
                await syncRewardsDataFromBackend();
                await syncMissionsFromBackend();
                originalInit();
                
                const claimBtn = document.getElementById("btn-claim-daily");
                if (claimBtn) {
                    const newBtn = claimBtn.cloneNode(true);
                    claimBtn.parentNode.replaceChild(newBtn, claimBtn);
                    newBtn.addEventListener("click", claimDailyReward);
                }
                
                const tabMilestones = document.getElementById("tab-milestones");
                const tabMissions = document.getElementById("tab-missions");
                const panelTitle = document.getElementById("panel-rewards-title");
                const milestonesContainer = document.getElementById("level-milestones-container");
                const missionsContainer = document.getElementById("missions-container");
                const missionFilters = document.getElementById("mission-type-filters");

                if (tabMilestones && tabMissions) {
                    tabMilestones.addEventListener("click", () => {
                        tabMilestones.classList.add("active");
                        tabMissions.classList.remove("active");
                        if (panelTitle) panelTitle.textContent = "🏆 Level Milestones";
                        if (milestonesContainer) milestonesContainer.style.display = "block";
                        if (missionsContainer) missionsContainer.style.display = "none";
                        if (missionFilters) missionFilters.style.display = "none";
                    });

                    tabMissions.addEventListener("click", () => {
                        tabMissions.classList.add("active");
                        tabMilestones.classList.remove("active");
                        if (panelTitle) panelTitle.textContent = "🎯 Quest Missions";
                        if (milestonesContainer) milestonesContainer.style.display = "none";
                        if (missionsContainer) missionsContainer.style.display = "block";
                        if (missionFilters) missionFilters.style.display = "flex";
                    });
                }

                const filterPills = document.querySelectorAll("#mission-type-filters .btn-page");
                filterPills.forEach(pill => {
                    pill.addEventListener("click", () => {
                        filterPills.forEach(p => p.classList.remove("active"));
                        pill.classList.add("active");
                        const targetType = pill.getAttribute("data-type");
                        if (window.filterMissionsByType) {
                            window.filterMissionsByType(targetType);
                        }
                    });
                });
            };
        }
        if (window.initRewardsPage) window.initRewardsPage();
    }
});
