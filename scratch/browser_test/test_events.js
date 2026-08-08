const puppeteer = require('puppeteer-core');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const EVENTS_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/events.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

async function runTest() {
  console.log('Starting events.html E2E test for click interactions...');

  // 1. Generate new test user credentials
  const username = `e2e_test_${Date.now()}@pokemonnexus.com`;
  const trainerName = `E2ETester_${Date.now().toString().slice(-4)}`;
  const password = 'trainerpass123';

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

  // Log in to get JWT token
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

  // Inject login credentials
  await page.evaluateOnNewDocument((tok, usr) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
  }, token, userPayload);

  console.log('Navigating to events.html...');
  await page.goto(`file:///${EVENTS_PATH}`, { waitUntil: 'networkidle2' });

  // Wait 2 seconds
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Check initial events joined count (should be 18)
  const initialCount = await page.evaluate(() => document.getElementById('stats-joined').textContent);
  console.log('Initial Events Joined Count:', initialCount);

  // Click the main featured JOIN EVENT button
  console.log('Clicking featured Join Event button...');
  await page.click('.btn-gradient.btn-orange');

  // Wait 1 second
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Check count after featured join (should be 19)
  const countAfterFeatured = await page.evaluate(() => document.getElementById('stats-joined').textContent);
  console.log('Events Joined Count after joining featured:', countAfterFeatured);

  // Click the Rayquaza Join Raid card button
  console.log('Clicking Rayquaza Join Raid card button...');
  await page.evaluate(() => {
    const btns = document.querySelectorAll('.btn-card');
    // Find Rayquaza button
    for (let btn of btns) {
      if (btn.textContent.includes('Join Raid')) {
        btn.click();
        break;
      }
    }
  });

  // Wait 1 second
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Check count after Rayquaza join (should be 20)
  const countAfterBoth = await page.evaluate(() => document.getElementById('stats-joined').textContent);
  console.log('Events Joined Count after joining both:', countAfterBoth);

  // Check localStorage contents
  const localVal = await page.evaluate(() => localStorage.getItem('pokemonNexusJoinedEvents'));
  console.log('localStorage pokemonNexusJoinedEvents content:', localVal);

  console.log('Taking clicked state screenshot...');
  const screenshotPath = 'C:\\Users\\simha\\.gemini\\antigravity\\brain\\25a83453-80fa-4f95-9063-1aa53533ed06\\events_clicked_screenshot.png';
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log(`Screenshot saved to: ${screenshotPath}`);

  console.log('Closing browser...');
  await browser.close();
}

runTest().catch(console.error);
