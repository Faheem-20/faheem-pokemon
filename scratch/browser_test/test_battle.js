const puppeteer = require('puppeteer-core');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BATTLE_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/battle.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

async function runTest() {
  console.log('Starting battle.html E2E test...');

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

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();

  page.on('console', msg => {
    console.log(`PAGE CONSOLE: [${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', err => {
    console.error(`PAGE ERROR: ${err.message}`);
  });

  // Inject real login credentials before navigation
  await page.evaluateOnNewDocument((tok, usr) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
  }, token, userPayload);

  console.log('Navigating to battle.html...');
  await page.goto(`file:///${BATTLE_PATH}`, { waitUntil: 'networkidle2' });

  // Wait 3 seconds for backend syncing and initial rendering
  await new Promise(resolve => setTimeout(resolve, 3000));

  console.log('Checking initial team loaded in window.playerTeamData:');
  const team = await page.evaluate(() => {
    return window.playerTeamData ? window.playerTeamData.map(p => ({
      name: p.name,
      hp: p.hp,
      maxHp: p.maxHp,
      moves: p.moves
    })) : [];
  });
  console.log(JSON.stringify(team, null, 2));

  // Let's print out the active player pokemon index
  const activeIdx = await page.evaluate(() => window.activePlayerPkmnIndex);
  console.log('Active Pokémon index:', activeIdx);

  // Let's try executing Thunderbolt (index 0)
  console.log('Clicking FIGHT for Thunderbolt...');
  await page.evaluate(() => {
    const fightBtn = document.querySelector('.hex-fight-btn');
    if (fightBtn) fightBtn.click();
  });

  await new Promise(resolve => setTimeout(resolve, 4000));

  // Let's try switching to Charizard (index 1) if available
  console.log('Attempting to switch to Charizard (index 1)...');
  const clickedSwitch = await page.evaluate(() => {
    const cards = document.querySelectorAll('.team-member-card');
    if (cards[1]) {
      cards[1].click();
      return true;
    }
    return false;
  });
  console.log('Clicked Charizard card:', clickedSwitch);

  await new Promise(resolve => setTimeout(resolve, 2000));

  // Print current active pokemon name after switch attempt
  const activeName = await page.evaluate(() => {
    const p = window.playerTeamData[window.activePlayerPkmnIndex];
    return p ? p.name : 'None';
  });
  console.log('Active Pokémon after switch attempt:', activeName);

  console.log('Closing browser...');
  await browser.close();
}

runTest().catch(console.error);
