const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const FRONTEND_PATH = 'c:/Users/simha/Downloads/Pokemon_Nexus_Complete_Project/Pokeman/achievements.html';
const BACKEND_URL = 'http://127.0.0.1:5000/api';

async function runVerification() {
  console.log('Starting Browser-based E2E Verification...');

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

  // 2. Launch browser with remote debugging
  console.log('Launching headless Chrome...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();

  // Monitor console errors and warnings
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (txt.includes('status of 400 (Bad Request)') || txt.includes('400')) {
        return; // ignore expected HTTP 400 error from duplicate claim check
      }
      consoleErrors.push(txt);
      console.error(`PAGE CONSOLE ERROR: ${txt}`);
    } else {
      console.log(`PAGE CONSOLE: ${msg.text()}`);
    }
  });

  // Monitor failed requests
  const failedRequests = [];
  page.on('requestfailed', request => {
    failedRequests.push(`${request.url()} - ${request.failure().errorText}`);
    console.error(`PAGE REQUEST FAILED: ${request.url()} - ${request.failure().errorText}`);
  });

  // Inject LocalStorage login state before navigation
  console.log('Pre-injecting session credentials into LocalStorage...');
  await page.evaluateOnNewDocument((tok, usr) => {
    localStorage.setItem('pokemonNexusAccess', tok);
    localStorage.setItem('pokemonNexusToken', tok);
    localStorage.setItem('pokemonNexusUser', JSON.stringify(usr));
  }, token, userPayload);

  // Navigate to achievements page file URI
  console.log(`Navigating to frontend achievements page...`);
  await page.goto(`file:///${FRONTEND_PATH}`, { waitUntil: 'networkidle2' });

  // 3. Verify page loads correctly with initial locked states
  console.log('Verifying initial achievements stats and locked states...');
  const initialStats = await page.evaluate(() => {
    const total = document.getElementById('stats-total').textContent.trim();
    const unlocked = document.getElementById('stats-unlocked').textContent.trim();
    
    // Find First Victory card status and locks
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const firstVictoryCard = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    
    const isLockedCard = firstVictoryCard ? firstVictoryCard.classList.contains('locked-card') : false;
    const btnText = firstVictoryCard ? firstVictoryCard.querySelector('.card-btn')?.textContent.trim() : '';
    const hasLockGlow = firstVictoryCard ? !!getComputedStyle(firstVictoryCard.querySelector('.badge-container'), '::after').content : false;

    return { total, unlocked, isLockedCard, btnText, hasLockGlow };
  });

  console.log('Initial stats check:', initialStats);
  if (initialStats.btnText.toUpperCase() !== 'LOCKED') {
    throw new Error(`Expected First Victory achievement to be LOCKED initially, but card class/button mismatch found: ${initialStats.btnText}`);
  }
  console.log('Passed Initial Locked State validation!');

  // 4. Record battle win to unlock First Victory
  console.log('Recording a battle victory for the trainer...');
  const battleRecord = await page.evaluate(async (tok, tName) => {
    const res = await fetch('http://127.0.0.1:5000/api/battles/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tok}`
      },
      body: JSON.stringify({
        opponent: 'Wild Pikachu',
        arena: 'Grassland Arena',
        weather: 'Sunny',
        battle_type: 'wild',
        winner: tName,
        loser: 'Wild Pikachu',
        started_at: new Date().toISOString()
      })
    });
    return res.ok ? await res.json() : null;
  }, token, trainerName);

  if (!battleRecord) {
    throw new Error('Failed to record battle victory via page fetch context.');
  }
  console.log('Battle recorded successfully! Reloading achievements dashboard...');

  // Reload page to reflect updated battle win progress
  await page.reload({ waitUntil: 'networkidle2' });

  // 5. Verify First Victory changed to CLAIM REWARD state
  const unlockStats = await page.evaluate(() => {
    const unlocked = document.getElementById('stats-unlocked').textContent.trim();
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const firstVictoryCard = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const isClaimableCard = firstVictoryCard ? firstVictoryCard.classList.contains('claimable-card') : false;
    const btnText = firstVictoryCard ? firstVictoryCard.querySelector('.card-btn')?.textContent.trim() : '';

    // Extract dynamic ID from the button's onclick attribute
    const btn = firstVictoryCard ? firstVictoryCard.querySelector('.card-btn') : null;
    const onclickStr = btn ? btn.getAttribute('onclick') || '' : '';
    const match = onclickStr.match(/claimReward\('([^']+)'\)/);
    const achId = match ? match[1] : null;

    return { unlocked, isClaimableCard, btnText, achId };
  });

  console.log('Unlock stats check:', unlockStats);
  const initialUnlocked = parseInt(initialStats.unlocked);
  if (parseInt(unlockStats.unlocked) !== initialUnlocked + 1) {
    throw new Error(`Expected ${initialUnlocked + 1} unlocked achievements, but got: ${unlockStats.unlocked}`);
  }
  if (unlockStats.btnText.toUpperCase() !== 'CLAIM REWARD') {
    throw new Error(`Expected First Victory card state to become CLAIM REWARD, but got: ${unlockStats.btnText}`);
  }
  console.log('Passed Battle Unlock Condition validation!');

  // 6. Click Claim Reward button and trigger claim celebration flow
  console.log('Clicking Claim Reward button to claim XP, Coins, and Crystals...');
  await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const firstVictoryCard = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const btn = firstVictoryCard ? firstVictoryCard.querySelector('.card-btn') : null;
    if (btn) btn.click();
  });

  // Wait for celebration and reload timeout
  console.log('Waiting for claim celebration animations and dynamic reloading...');
  await new Promise(resolve => setTimeout(resolve, 4000));

  // 7. Verify claimed status, profile stats updates, and reward history updates
  const claimedStats = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const firstVictoryCard = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const isClaimedCard = firstVictoryCard ? firstVictoryCard.classList.contains('claimed-card') : false;
    const btnText = firstVictoryCard ? firstVictoryCard.querySelector('.card-btn')?.textContent.trim() : '';
    
    // Check summary card updates
    const xp = document.getElementById('stats-xp').textContent.trim();
    const crystals = document.getElementById('stats-crystals').textContent.trim();
    const claimedCount = document.getElementById('stats-unlocked').textContent.trim();

    return { isClaimedCard, btnText, xp, crystals, claimedCount };
  });

  console.log('Claimed stats check:', claimedStats);
  if (claimedStats.btnText.toUpperCase() !== 'CLAIMED') {
    throw new Error(`Expected First Victory to show CLAIMED state, but got: ${claimedStats.btnText}`);
  }
  if (parseInt(claimedStats.xp) !== 50 || parseInt(claimedStats.crystals) !== 10) {
    throw new Error(`Expected 50 XP and 10 Crystals in summary, but got XP: ${claimedStats.xp}, Crystals: ${claimedStats.crystals}`);
  }
  console.log('Passed Reward Distribution and UI updates without refresh validation!');

  // 8. Refresh page to verify database persistence
  console.log('Refreshing the page to verify persistence...');
  await page.reload({ waitUntil: 'networkidle2' });

  const persistStats = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.achievement-card'));
    const firstVictoryCard = cards.find(c => c.querySelector('.achievement-title')?.textContent.trim() === 'First Victory');
    const btnText = firstVictoryCard ? firstVictoryCard.querySelector('.card-btn')?.textContent.trim() : '';
    return { btnText };
  });

  console.log('Persistence check:', persistStats);
  if (persistStats.btnText.toUpperCase() !== 'CLAIMED') {
    throw new Error(`Expected First Victory to remain CLAIMED after refresh, but got: ${persistStats.btnText}`);
  }
  console.log('Passed Database & Refresh Persistence validation!');

  // 9. Block duplicate claim check
  console.log(`Verifying duplicate claims are blocked for achievement ID: ${unlockStats.achId}...`);
  const doubleClaimRes = await page.evaluate(async (tok, achId) => {
    const res = await fetch('http://127.0.0.1:5000/api/achievements/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tok}`
      },
      body: JSON.stringify({ achievement_id: achId })
    });
    return { ok: res.ok, status: res.status, text: await res.text() };
  }, token, unlockStats.achId);

  console.log('Duplicate claim response:', doubleClaimRes);
  if (doubleClaimRes.ok || doubleClaimRes.status !== 400) {
    throw new Error(`Expected duplicate claim to be blocked with HTTP 400, but got: ${doubleClaimRes.status}`);
  }
  console.log('Passed Duplicate Claim Prevention validation!');

  // Clean up browser instance
  await browser.close();

  // Final check on logs
  console.log('Asserting zero console errors or failed requests...');
  if (consoleErrors.length > 0) {
    throw new Error(`Test encountered console errors: ${consoleErrors.join(', ')}`);
  }
  if (failedRequests.length > 0) {
    throw new Error(`Test encountered failed network requests: ${failedRequests.join(', ')}`);
  }

  console.log('\n======================================');
  console.log('  ALL BROWSER E2E VERIFICATIONS PASSED');
  console.log('======================================\n');
  return true;
}

runVerification().catch(err => {
  console.error('\n======================================');
  console.log('  BROWSER E2E VERIFICATION FAILED');
  console.log('======================================\n');
  console.error(err);
  process.exit(1);
});
