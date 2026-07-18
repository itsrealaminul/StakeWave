/* StakeWave — Main Application JS */
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://stakewave.up.railway.app';

let userToken = null;
let userData = null;

// Telegram WebApp Init
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#0F0F1A');
    tg.setBackgroundColor('#0F0F1A');
}

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupNavigation();
    setupFilters();
    await authenticate();
    loadHome();
}

// Auth
async function authenticate() {
    const initData = tg?.initData || '';
    const user = tg?.initDataUnsafe?.user;

    try {
        const refCode = new URLSearchParams(window.location.search).get('ref') ||
                        new URLSearchParams(window.location.hash.slice(1)).get('ref');

        const res = await fetch(`${API_URL}/api/user/auth`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                telegram_id: user?.id || Math.floor(Math.random() * 1000000),
                username: user?.username || 'test_user',
                first_name: user?.first_name || 'User',
                referral_code: refCode
            })
        });
        const data = await res.json();
        userToken = data.token;
        userData = data.user;
        updateUI();
    } catch (e) {
        console.error('Auth error:', e);
        showToast('Connection error. Please try again.', 'error');
    }
}

function updateUI() {
    if (!userData) return;
    document.getElementById('balance').textContent = `$${userData.balance.toFixed(2)}`;
    document.getElementById('username').textContent = userData.username || userData.first_name;
    document.getElementById('level').textContent = `Lv.${userData.level}`;
    document.getElementById('streak').textContent = `🔥 ${userData.daily_streak}`;
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

            if (btn.dataset.tab === 'predict') loadPredictions();
            if (btn.dataset.tab === 'stake') loadStakes();
            if (btn.dataset.tab === 'tasks') loadTasks();
        });
    });
}

function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadPredictions(btn.dataset.filter);
        });
    });
}

// Home
async function loadHome() {
    await Promise.all([loadHotPredictions(), loadQuickTasks()]);
}

async function loadHotPredictions() {
    try {
        const res = await fetch(`${API_URL}/api/predictions/active`);
        const predictions = await res.json();
        const container = document.getElementById('hot-predictions');
        container.innerHTML = predictions.slice(0, 3).map(p => predictionCard(p)).join('');
    } catch (e) { console.error(e); }
}

async function loadQuickTasks() {
    try {
        const res = await fetch(`${API_URL}/api/tasks/available?token=${userToken}`);
        const tasks = await res.json();
        const container = document.getElementById('quick-tasks');
        container.innerHTML = tasks.slice(0, 3).map(t => taskCard(t)).join('');
    } catch (e) { console.error(e); }
}

// Predictions
async function loadPredictions(filter = 'all') {
    try {
        const res = await fetch(`${API_URL}/api/predictions/active`);
        let predictions = await res.json();
        if (filter !== 'all') predictions = predictions.filter(p => p.category === filter);

        document.getElementById('predictions-list').innerHTML = predictions.map(p => predictionCard(p)).join('');
        loadMyBets();
    } catch (e) { console.error(e); }
}

function predictionCard(p) {
    const total = p.total_pool || 0;
    const pctA = total > 0 ? ((p.total_pool_a / total) * 100).toFixed(0) : 50;
    const pctB = total > 0 ? ((p.total_pool_b / total) * 100).toFixed(0) : 50;
    return `
        <div class="prediction-card">
            <div class="category">${p.category || 'prediction'}</div>
            <h4>${p.title}</h4>
            <div class="pool-info">
                <span>Pool: $${total.toFixed(2)}</span>
                <span>Ends: ${new Date(p.end_time).toLocaleDateString()}</span>
            </div>
            <div class="options">
                <button class="option-btn opt-a" onclick="openBetModal(${p.id}, '${p.option_a}', 'A', ${p.min_bet})">
                    ${p.option_a}<span class="pool">${pctA}% · $${p.total_pool_a.toFixed(2)}</span>
                </button>
                <button class="option-btn opt-b" onclick="openBetModal(${p.id}, '${p.option_b}', 'B', ${p.min_bet})">
                    ${p.option_b}<span class="pool">${pctB}% · $${p.total_pool_b.toFixed(2)}</span>
                </button>
            </div>
        </div>`;
}

function openBetModal(predId, optionName, option, minBet) {
    document.getElementById('predict-title').textContent = 'Place Your Bet';
    document.getElementById('predict-body').innerHTML = `
        <p style="margin-bottom:16px;color:var(--text-secondary)">Betting on: <strong>${optionName}</strong></p>
        <input type="number" id="bet-amount" placeholder="Bet amount ($${minBet}+)" min="${minBet}" step="0.01"
            style="width:100%;padding:14px;border-radius:12px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:16px;margin-bottom:12px">
        <button class="btn-primary" onclick="placeBet(${predId}, '${option}')">🔮 Place Bet</button>`;
    openModal('predict-modal');
}

async function placeBet(predId, option) {
    const amount = parseFloat(document.getElementById('bet-amount').value);
    if (!amount || amount <= 0) return showToast('Enter valid amount', 'error');

    try {
        const res = await fetch(`${API_URL}/api/predictions/bet?token=${userToken}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prediction_id: predId, option, amount })
        });
        const data = await res.json();
        if (res.ok) {
            userData.balance = data.new_balance;
            updateUI();
            closeModal('predict-modal');
            showToast(`Bet placed! Potential payout: $${data.potential_payout}`, 'success');
            loadPredictions();
        } else {
            showToast(data.detail || 'Error placing bet', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
}

async function loadMyBets() {
    try {
        const res = await fetch(`${API_URL}/api/predictions/my-bets?token=${userToken}`);
        const bets = await res.json();
        const container = document.getElementById('my-bets');
        if (!bets.length) { container.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:20px">No bets yet</p>'; return; }
        container.innerHTML = bets.map(b => `
            <div class="bet-card">
                <h4>${b.prediction_title}</h4>
                <div class="bet-info">
                    <span>Option: ${b.option} · $${b.amount}</span>
                    <span>Potential: $${b.potential_payout}</span>
                    <span class="status-${b.status}">${b.status}</span>
                </div>
            </div>`).join('');
    } catch (e) { console.error(e); }
}

// Staking
async function createStake() {
    const amount = parseFloat(document.getElementById('stake-amount').value);
    if (!amount || amount < 0.10) return showToast('Minimum stake: $0.10', 'error');

    try {
        const res = await fetch(`${API_URL}/api/staking/stake?token=${userToken}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });
        const data = await res.json();
        if (res.ok) {
            userData.balance = data.balance;
            updateUI();
            document.getElementById('stake-amount').value = '';
            showToast(`Staked $${amount} at ${data.apy}% APY!`, 'success');
            loadStakes();
        } else {
            showToast(data.detail || 'Error', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
}

async function loadStakes() {
    try {
        const res = await fetch(`${API_URL}/api/staking/my-stakes?token=${userToken}`);
        const stakes = await res.json();
        const container = document.getElementById('my-stakes');
        if (!stakes.length) { container.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:20px">No active stakes</p>'; return; }
        container.innerHTML = stakes.map(s => `
            <div class="stake-card">
                <div class="stake-header">
                    <span class="stake-amount">$${s.amount.toFixed(2)}</span>
                    <span class="stake-status ${s.status}">${s.status}</span>
                </div>
                <div style="font-size:12px;color:var(--text-secondary)">
                    APY: ${s.apy}% · Earned: $${s.earned_so_far.toFixed(4)}
                </div>
                ${s.status === 'active' ? `<button class="unstake-btn" onclick="unstake(${s.id})">💸 Unstake + Collect</button>` : ''}
            </div>`).join('');
    } catch (e) { console.error(e); }
}

async function unstake(stakeId) {
    try {
        const res = await fetch(`${API_URL}/api/staking/unstake?token=${userToken}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stake_id: stakeId })
        });
        const data = await res.json();
        if (res.ok) {
            userData.balance = data.balance;
            updateUI();
            showToast(`Unstaked! Return: $${data.total_return}`, 'success');
            loadStakes();
        } else {
            showToast(data.detail || 'Error', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
}

// Tasks
async function loadTasks() {
    try {
        const res = await fetch(`${API_URL}/api/tasks/available?token=${userToken}`);
        const tasks = await res.json();
        document.getElementById('tasks-list').innerHTML = tasks.map(t => taskCard(t)).join('');
    } catch (e) { console.error(e); }
}

function taskCard(t) {
    return `
        <div class="task-card">
            <div class="task-info">
                <h4>${t.title}</h4>
                <div class="task-type">${t.task_type} · ${t.description || ''}</div>
            </div>
            <button class="task-reward" onclick="completeTask(${t.id})">+$${t.reward.toFixed(2)}</button>
        </div>`;
}

async function completeTask(taskId) {
    try {
        const res = await fetch(`${API_URL}/api/tasks/complete?token=${userToken}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId })
        });
        const data = await res.json();
        if (res.ok) {
            userData.balance = data.balance;
            updateUI();
            showToast(`+$${data.reward.toFixed(2)} earned!`, 'success');
            loadTasks();
        } else {
            showToast(data.detail || 'Already completed', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
}

// Daily Claim
async function claimDaily() {
    try {
        const res = await fetch(`${API_URL}/api/user/daily-claim?token=${userToken}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            userData.balance = data.balance;
            userData.daily_streak = data.streak;
            updateUI();
            showToast(`+$${data.reward.toFixed(2)} daily reward! 🔥${data.streak} streak`, 'success');
        } else {
            showToast(data.detail || 'Already claimed today', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
}

// Spin
function openSpin() {
    openModal('spin-modal');
    drawSpinWheel();
}

function drawSpinWheel() {
    const canvas = document.getElementById('spin-wheel');
    const ctx = canvas.getContext('2d');
    const rewards = [
        { label: '$0.01', color: '#4CAF50' },
        { label: '$0.02', color: '#2196F3' },
        { label: '$0.05', color: '#FF9800' },
        { label: '$0.10', color: '#9C27B0' },
        { label: '$0.25', color: '#F44336' },
        { label: '$0.50', color: '#E91E63' },
        { label: '$1.00', color: '#FFD700' },
        { label: '$5.00', color: '#FF0000' }
    ];
    const sliceAngle = (2 * Math.PI) / rewards.length;
    const cx = 150, cy = 150, r = 140;

    ctx.clearRect(0, 0, 300, 300);
    rewards.forEach((rw, i) => {
        const startAngle = i * sliceAngle - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, startAngle, startAngle + sliceAngle);
        ctx.fillStyle = rw.color;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(startAngle + sliceAngle / 2);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 13px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(rw.label, r * 0.6, 5);
        ctx.restore();
    });
}

async function doSpin() {
    document.getElementById('spin-go').disabled = true;
    try {
        const res = await fetch(`${API_URL}/api/user/spin?token=${userToken}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            userData.balance = data.balance;
            updateUI();
            document.getElementById('spin-result').innerHTML = `🎉 You won <span style="color:var(--success)">$${data.reward.toFixed(2)}</span>!`;
            showToast(`Won $${data.reward.toFixed(2)}!`, 'success');
        } else {
            showToast(data.detail || 'Spin error', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
    document.getElementById('spin-go').disabled = false;
}

// Referral
function openReferral() {
    const botUsername = 'StakeWave_Bot';
    const refCode = userData?.referral_code || '';
    document.getElementById('referral-link').value = `https://t.me/${botUsername}?start=ref_${refCode}`;
    document.getElementById('ref-count').textContent = userData?.referral_count || 0;
    document.getElementById('ref-earned').textContent = `$${(userData?.referral_earnings || 0).toFixed(2)}`;
    openModal('referral-modal');
}

function copyReferral() {
    const input = document.getElementById('referral-link');
    input.select();
    document.execCommand('copy');
    showToast('Referral link copied!', 'success');
}

// Leaderboard
async function openLeaderboard() {
    openModal('leaderboard-modal');
    try {
        const res = await fetch(`${API_URL}/api/predictions/leaderboard`);
        const lb = await res.json();
        document.getElementById('leaderboard-body').innerHTML = lb.map(u => `
            <div class="lb-item">
                <span class="rank">${u.rank <= 3 ? ['🥇','🥈','🥉'][u.rank-1] : u.rank}</span>
                <span class="name">${u.username}</span>
                <span class="earned">$${u.total_earned.toFixed(2)}</span>
            </div>`).join('') || '<p style="text-align:center;color:var(--text-secondary)">No data yet</p>';
    } catch (e) { console.error(e); }
}

// Modals
function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// Toast
function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = `toast show ${type}`;
    setTimeout(() => toast.className = 'toast', 3000);
}

// Placeholder functions
function showHistory() { showToast('Coming soon!', 'success'); }
function showWithdraw() { showToast('Withdrawals coming soon!', 'success'); }
function showSettings() { showToast('Settings coming soon!', 'success'); }
