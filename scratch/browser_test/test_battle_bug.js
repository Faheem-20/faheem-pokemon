const puppeteer = require('puppeteer-core');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BATTLE_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/battle.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

async function runTest() {
  console.log('Starting battle.html bug replication...');

  // Register and login test user
  const username = `e2e_test_${Date.now()}@pokemonnexus.com`;
  const trainerName = `BattleBug_${Date.now().toString().slice(-4)}`;
  const password = 'trainerpass123';

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
    throw new Error(`Failed to register: ${errText}`);
  }

  const loginRes = await fetch(`${BACKEND_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: username,
      password: password
    })
  });

  const tokenData = await loginRes.json();
  const token = tokenData.access || tokenData.token;
  const userPayload = tokenData.user;

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  page.on('console', msg => {
    console.log(`PAGE CONSOLE: [${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', err => {
    console.error(`PAGE ERROR STACK: ${err.stack}`);
  });

  await page.evaluateOnNewDocument((tok, usr) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
  }, token, userPayload);

  console.log('Navigating to battle.html...');
  await page.goto(`file:///${BATTLE_PATH}`, { waitUntil: 'networkidle2' });

  // Wait 2 seconds
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Get initial inventory HTML
  const initialInv = await page.evaluate(() => document.getElementById('bag-sidebar-list').innerHTML.trim());
  console.log('Initial Inventory HTML length:', initialInv.length);

  // Click Charizard card in the sidebar (index 1)
  console.log('Clicking Charizard (index 1) in sidebar...');
  await page.evaluate(() => {
    const cards = document.querySelectorAll('.team-member-card');
    if (cards[1]) cards[1].click();
  });

  // Wait 1 second
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Get inventory HTML after click
  const afterClickInv = await page.evaluate(() => document.getElementById('bag-sidebar-list').innerHTML.trim());
  console.log('Inventory HTML length after clicking Pokémon:', afterClickInv.length);
  console.log('Inventory HTML content after click:', afterClickInv);

  console.log('Closing browser...');
  await browser.close();
}

runTest().catch(console.error);
