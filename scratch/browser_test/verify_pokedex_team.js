const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const POKEDEX_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/pokedex.html';
const PROFILE_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/profile.html';
const BATTLE_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/battle.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

const mockPokedex = [
  { id: 1, name: "Bulbasaur", types: ["grass", "poison"], artwork: "", hp: 45, attack: 49, defense: 49, speed: 45, moves: ["Tackle", "Growl"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/1/" },
  { id: 2, name: "Ivysaur", types: ["grass", "poison"], artwork: "", hp: 60, attack: 62, defense: 63, speed: 60, moves: ["Tackle", "Growl"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/2/" },
  { id: 3, name: "Venusaur", types: ["grass", "poison"], artwork: "", hp: 80, attack: 82, defense: 83, speed: 80, moves: ["Tackle", "Growl"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/3/" },
  { id: 4, name: "Charmander", types: ["fire"], artwork: "", hp: 39, attack: 52, defense: 43, speed: 65, moves: ["Scratch", "Growl"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/4/" },
  { id: 5, name: "Charmeleon", types: ["fire"], artwork: "", hp: 58, attack: 64, defense: 58, speed: 80, moves: ["Scratch", "Growl"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/5/" },
  { id: 6, name: "Charizard", types: ["fire", "flying"], artwork: "", hp: 78, attack: 84, defense: 78, speed: 100, moves: ["Scratch", "Growl"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/6/" },
  { id: 7, name: "Squirtle", types: ["water"], artwork: "", hp: 44, attack: 48, defense: 65, speed: 43, moves: ["Tackle", "Tail Whip"], speciesUrl: "https://pokeapi.co/api/v2/pokemon-species/7/" }
];

async function runTeamVerification() {
  console.log('Starting Pokédex Team integration E2E Verification...');

  // 1. Generate new test user credentials
  const username = `e2e_test_${Date.now()}@pokemonnexus.com`;
  const trainerName = `E2ETester_${Date.now().toString().slice(-4)}`;
  const password = 'trainerpass123';

  console.log(`Registering new test trainer: ${trainerName} (${username})...`);

  // Register user via Backend API
  const registerRes = await fetch(`${BACKEND_URL}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: username,
      password: password,
      confirmPassword: password,
      trainerName: trainerName
    })
  });

  if (!registerRes.ok) {
    const errText = await registerRes.text();
    throw new Error(`Failed to register test user: ${errText}`);
  }
  console.log('Registration successful!');

  // Log in to get JWT token
  console.log('Logging in to retrieve JWT access tokens...');
  const loginRes = await fetch(`${BACKEND_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: username,
      password: password
    })
  });

  if (!loginRes.ok) {
    const errText = await loginRes.text();
    throw new Error(`Failed to log in: ${errText}`);
  }

  const tokenData = await loginRes.json();
  const token = tokenData.access || tokenData.token;
  const userPayload = tokenData.user;
  console.log('Login successful! Token retrieved.');

  // Launch headless Chrome
  console.log('Launching headless Chrome...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();

  // Monitor console
  page.on('console', msg => {
    console.log(`PAGE CONSOLE: ${msg.text()}`);
  });

  // Pre-inject session credentials and Mock Pokedex into LocalStorage
  console.log('Pre-injecting session credentials and Mock Pokédex into LocalStorage...');
  await page.evaluateOnNewDocument((tok, usr, mockData) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
    localStorage.setItem('pokemonNexus_pokedex_152', JSON.stringify(mockData));
  }, token, userPayload, mockPokedex);

  // 1. Load pokedex page
  console.log('Navigating to Pokédex page...');
  await page.goto(`file:///${POKEDEX_PATH}`, { waitUntil: 'networkidle2' });

  // Clear team cache once initially
  await page.evaluate(() => {
    localStorage.removeItem("pokemonNexusTeam");
  });

  // Reload to ensure clean slate with empty team
  await page.reload({ waitUntil: 'networkidle2' });

  // Wait for the pokémon cards to load and render
  console.log('Waiting for poke-card elements...');
  await page.waitForSelector('.poke-card', { timeout: 15000 });
  console.log('Cards rendered successfully!');

  // Helper to get toast message
  async function getToastText() {
    return await page.evaluate(() => {
      const toast = document.getElementById('toast');
      return toast ? toast.textContent.trim() : '';
    });
  }

  // Helper to click "+ Team" / "+ TEAM" button by Pokémon name
  async function clickTeamButton(pokemonName) {
    console.log(`Clicking + TEAM button for ${pokemonName}...`);
    await page.evaluate((name) => {
      const cards = Array.from(document.querySelectorAll('.poke-card'));
      const pkmnCard = cards.find(c => c.querySelector('.poke-name').textContent.trim().toLowerCase() === name.toLowerCase());
      if (!pkmnCard) throw new Error(`Could not find card for ${name}`);
      const btn = Array.from(pkmnCard.querySelectorAll('button')).find(b => b.textContent.includes('Team') || b.textContent.includes('ADDED'));
      if (!btn) throw new Error(`Could not find team button for ${name}`);
      btn.click();
    }, pokemonName);
  }

  // Helper to get button text for a Pokémon card
  async function getButtonText(pokemonName) {
    return await page.evaluate((name) => {
      const cards = Array.from(document.querySelectorAll('.poke-card'));
      const pkmnCard = cards.find(c => c.querySelector('.poke-name').textContent.trim().toLowerCase() === name.toLowerCase());
      if (!pkmnCard) return '';
      const btn = Array.from(pkmnCard.querySelectorAll('button')).find(b => b.textContent.includes('Team') || b.textContent.includes('ADDED'));
      return btn ? btn.textContent.trim() : '';
    }, pokemonName);
  }

  // 2. Add Bulbasaur to team
  await clickTeamButton('Bulbasaur');
  
  // Wait a short bit for toast
  await new Promise(r => setTimeout(r, 400));
  const t1 = await getToastText();
  console.log(`Toast text for first add: "${t1}"`);
  if (t1 !== 'Bulbasaur added to team!') {
    throw new Error(`Expected toast to be "Bulbasaur added to team!", got "${t1}"`);
  }

  // Check button text is "ADDED"
  const b1 = await getButtonText('Bulbasaur');
  console.log(`Button text for Bulbasaur: "${b1}"`);
  if (b1 !== 'ADDED') {
    throw new Error(`Expected Bulbasaur button to say "ADDED", got "${b1}"`);
  }

  // 3. Try to add Bulbasaur again
  await clickTeamButton('Bulbasaur');
  await new Promise(r => setTimeout(r, 400));
  const t2 = await getToastText();
  console.log(`Toast text for duplicate add: "${t2}"`);
  if (t2 !== 'Bulbasaur is already in your team!') {
    throw new Error(`Expected toast to be "Bulbasaur is already in your team!", got "${t2}"`);
  }

  // 4. Fill the team (Ivysaur, Venusaur, Charmander, Charmeleon, Charizard)
  const pkmnToFill = ['Ivysaur', 'Venusaur', 'Charmander', 'Charmeleon', 'Charizard'];
  for (const name of pkmnToFill) {
    await clickTeamButton(name);
    await new Promise(r => setTimeout(r, 400));
    const t = await getToastText();
    console.log(`Added ${name}, toast: "${t}"`);
    if (t !== `${name} added to team!`) {
      throw new Error(`Expected toast to be "${name} added to team!", got "${t}"`);
    }
  }

  // 5. Try to add a 7th Pokémon (Squirtle)
  await clickTeamButton('Squirtle');
  await new Promise(r => setTimeout(r, 400));
  const t3 = await getToastText();
  console.log(`Toast text for 7th add: "${t3}"`);
  if (t3 !== 'Team is full! Remove one Pokémon first.') {
    throw new Error(`Expected toast to be "Team is full! Remove one Pokémon first.", got "${t3}"`);
  }

  // 6. Refresh page and verify ADDED states persist
  console.log('Refreshing Pokédex page to verify persistence...');
  await page.reload({ waitUntil: 'networkidle2' });

  // Wait again for cards
  await page.waitForSelector('.poke-card');

  const bPersist = await getButtonText('Bulbasaur');
  console.log(`Bulbasaur button text after refresh: "${bPersist}"`);
  if (bPersist !== 'ADDED') {
    throw new Error(`Expected Bulbasaur button to remain "ADDED" after refresh, got "${bPersist}"`);
  }

  // 7. Verify Profile Page reads the same team data
  console.log('Navigating to Profile page...');
  await page.goto(`file:///${PROFILE_PATH}`, { waitUntil: 'networkidle2' });

  const profileTeamList = await page.evaluate(() => {
    const slots = Array.from(document.querySelectorAll('.team-pkmn-slot'));
    return slots.map(s => s.querySelector('.team-pkmn-name')?.textContent.trim());
  });

  console.log('Profile page active team:', profileTeamList);
  const expectedTeam = ['Bulbasaur', 'Ivysaur', 'Venusaur', 'Charmander', 'Charmeleon', 'Charizard'];
  for (const name of expectedTeam) {
    if (!profileTeamList.includes(name)) {
      throw new Error(`Expected Profile team to contain ${name}, but got: ${profileTeamList.join(', ')}`);
    }
  }
  console.log('Passed Profile Page team verification!');

  // 8. Verify Battle Page reads the same team data
  console.log('Navigating to Battle page...');
  await page.goto(`file:///${BATTLE_PATH}`, { waitUntil: 'networkidle2' });

  const battleTeamList = await page.evaluate(() => {
    return window.playerTeamData ? window.playerTeamData.map(p => p.name) : [];
  });

  console.log('Battle page player team data:', battleTeamList);
  for (const name of expectedTeam) {
    if (!battleTeamList.includes(name)) {
      throw new Error(`Expected Battle team to contain ${name}, but got: ${battleTeamList.join(', ')}`);
    }
  }
  console.log('Passed Battle Page team verification!');

  console.log('Closing browser...');
  await browser.close();

  console.log('\n======================================================');
  console.log('  ALL POKEDEX TEAM INTEGRATION VERIFICATIONS PASSED');
  console.log('======================================================\n');
}

runTeamVerification().catch(err => {
  console.error('\n======================================================');
  console.log('  POKEDEX TEAM INTEGRATION VERIFICATION FAILED');
  console.log('======================================================\n');
  console.error(err);
  process.exit(1);
});
