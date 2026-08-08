const puppeteer = require('puppeteer-core');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const POKEDEX_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/pokedex.html';
const REWARDS_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/rewards.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

async function runTest() {
  console.log('Starting E2E navbar comparison test...');

  // Register and login test user
  const username = `e2e_test_${Date.now()}@pokemonnexus.com`;
  const trainerName = `NavbarTester_${Date.now().toString().slice(-4)}`;
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
    throw new Error(`Failed to register test user: ${errText}`);
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
    console.error(`PAGE ERROR: ${err.message}`);
  });

  // Inject credentials
  await page.evaluateOnNewDocument((tok, usr) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
  }, token, userPayload);

  // 1. Take Pokedex navbar screenshot
  console.log('Navigating to pokedex.html...');
  await page.goto(`file:///${POKEDEX_PATH}`, { waitUntil: 'networkidle2' });
  await new Promise(resolve => setTimeout(resolve, 2000));
  const pokedexScreenshotPath = 'C:\\Users\\simha\\.gemini\\antigravity\\brain\\25a83453-80fa-4f95-9063-1aa53533ed06\\pokedex_navbar.png';
  await page.screenshot({ path: pokedexScreenshotPath, fullPage: false });
  console.log(`Pokedex screenshot saved: ${pokedexScreenshotPath}`);

  // 2. Take Rewards navbar screenshot
  console.log('Navigating to rewards.html...');
  await page.goto(`file:///${REWARDS_PATH}`, { waitUntil: 'networkidle2' });
  await new Promise(resolve => setTimeout(resolve, 2000));
  const rewardsScreenshotPath = 'C:\\Users\\simha\\.gemini\\antigravity\\brain\\25a83453-80fa-4f95-9063-1aa53533ed06\\rewards_navbar.png';
  await page.screenshot({ path: rewardsScreenshotPath, fullPage: false });
  console.log(`Rewards screenshot saved: ${rewardsScreenshotPath}`);

  console.log('Closing browser...');
  await browser.close();
}

runTest().catch(console.error);
