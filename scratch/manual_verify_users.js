const puppeteer = require('puppeteer-core');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const FRONTEND_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/achievements.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

async function verifyUserFlow(username, password, isNewUser, trainerName = null) {
  let targetTrainerName = trainerName;

  if (isNewUser) {
    const timestamp = Date.now();
    username = `manual_new_${timestamp}@pokemonnexus.com`;
    targetTrainerName = `NewTrainer_${timestamp.toString().slice(-4)}`;
    password = 'password123';

    console.log(`\n[NEW USER] Registering: ${targetTrainerName} (${username})...`);
    const regRes = await fetch(`${BACKEND_URL}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: username,
        password: password,
        confirmPassword: password,
        trainerName: targetTrainerName
      })
    });
    if (!regRes.ok) throw new Error(`Registration failed: ${await regRes.text()}`);
  } else {
    console.log(`\n[EXISTING USER] Logging in: ${username}...`);
  }

  // Log in
  const loginRes = await fetch(`${BACKEND_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: username, password })
  });
  if (!loginRes.ok) throw new Error(`Login failed: ${await loginRes.text()}`);
  
  const tokenData = await loginRes.json();
  const token = tokenData.access;
  const userPayload = tokenData.user;
  if (!targetTrainerName) {
    targetTrainerName = userPayload.trainerName;
  }

  console.log(`Logged in successfully! Token acquired. Trainer Name: ${targetTrainerName}`);

  // Launch browser
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();

  // Inject token and user
  await page.evaluateOnNewDocument((tok, usr) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
  }, token, userPayload);

  // Load Achievements
  await page.goto(`file:///${FRONTEND_PATH}`, { waitUntil: 'networkidle2' });

  // 1. Initial State Check
  const initialWins = await page.evaluate(() => {
    const text = document.getElementById("debug-wins").textContent.trim();
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const fv = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const btn = fv ? fv.querySelector('.card-btn')?.textContent.trim() : 'NONE';
    return { wins: parseInt(text) || 0, btn };
  });

  console.log(`  Initial check -> Wins: ${initialWins.wins}, First Victory button: ${initialWins.btn}`);

  // 2. Submit Battle Victory
  console.log(`  Simulating battle victory...`);
  const battleRes = await page.evaluate(async (tok, tName) => {
    const res = await fetch('http://127.0.0.1:5000/api/battles/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tok}`
      },
      body: JSON.stringify({
        opponent: 'Wild Charizard',
        arena: 'Volcano Arena',
        weather: 'Sunny / Magma Storm',
        battle_type: 'wild',
        winner: tName,
        loser: 'Wild Charizard',
        is_win: true,
        xp_gained: 450,
        coins_gained: 150
      })
    });
    return res.ok ? await res.json() : null;
  }, token, targetTrainerName);

  if (!battleRes) throw new Error("Battle recording failed!");

  // Reload page
  await page.reload({ waitUntil: 'networkidle2' });

  // 3. Check unlocked state
  const unlockCheck = await page.evaluate(() => {
    const text = document.getElementById("debug-wins").textContent.trim();
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const fv = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const btn = fv ? fv.querySelector('.card-btn')?.textContent.trim() : 'NONE';
    return { wins: parseInt(text) || 0, btn };
  });

  console.log(`  After win -> Wins: ${unlockCheck.wins}, First Victory button: ${unlockCheck.btn}`);

  if (unlockCheck.wins <= initialWins.wins) {
    throw new Error(`Wins count did not increment! Staid at: ${unlockCheck.wins}`);
  }
  if (unlockCheck.btn.toUpperCase() !== 'CLAIM REWARD') {
    throw new Error(`Expected button state to be CLAIM REWARD, but got: ${unlockCheck.btn}`);
  }

  // 4. Claim Reward
  console.log(`  Claiming reward...`);
  await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const fv = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const btn = fv ? fv.querySelector('.card-btn') : null;
    if (btn) btn.click();
  });

  // Wait for animation & reload
  await new Promise(resolve => setTimeout(resolve, 2000));

  // 5. Final claimed state and persistence check
  await page.reload({ waitUntil: 'networkidle2' });

  const finalCheck = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const fv = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const btn = fv ? fv.querySelector('.card-btn')?.textContent.trim() : 'NONE';
    return { btn };
  });

  console.log(`  After claim & refresh -> First Victory button: ${finalCheck.btn}`);
  if (finalCheck.btn.toUpperCase() !== 'CLAIMED') {
    throw new Error(`Expected button state to be CLAIMED, but got: ${finalCheck.btn}`);
  }

  await browser.close();
  console.log(`[SUCCESS] Flow passed for user: ${username}`);
}

async function run() {
  try {
    // 1. Verify Existing User
    await verifyUserFlow('simham477@gmail.com', 'password123', false);

    // 2. Verify New User
    await verifyUserFlow(null, null, true);
    
    console.log('\n======================================');
    console.log('  ALL MANUAL VERIFICATIONS PASSED');
    console.log('======================================\n');
  } catch(e) {
    console.error("Verification failed:", e);
    process.exit(1);
  }
}

run();
