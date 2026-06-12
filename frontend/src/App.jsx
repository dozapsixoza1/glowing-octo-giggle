import { useState, useEffect, useCallback } from "react";

// ============================================================
// CONSTANTS & CONFIG
// ============================================================
const BACKEND = "https://automatic-funicular-ov9e.vercel.app"; // замени на свой URL

const RARITY_COLORS = {
  common: "#888",
  uncommon: "#4CAF50",
  rare: "#2196F3",
  epic: "#9C27B0",
  legendary: "#C8FF00",
};

const RARITY_LABELS = {
  common: "Обычный",
  uncommon: "Необычный",
  rare: "Редкий",
  epic: "Эпический",
  legendary: "ЛЕГЕНДАРНЫЙ",
};

// ============================================================
// API
// ============================================================
function getInitData() {
  return window.Telegram?.WebApp?.initData || "";
}

async function api(path, options = {}) {
  const res = await fetch(`${BACKEND}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-init-data": getInitData(),
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Ошибка сервера" }));
    throw new Error(err.detail || "Ошибка");
  }
  return res.json();
}

// ============================================================
// STYLES
// ============================================================
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  :root {
    --lime: #C8FF00;
    --lime-dim: #9ABF00;
    --bg: #0F0F08;
    --surface: #1A1A0F;
    --surface2: #242418;
    --border: #2D2D1A;
    --text: #F0F0D8;
    --muted: #666650;
    --danger: #FF4444;
    --gold: #FFD700;
  }

  html, body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; }
  
  .app {
    min-height: 100vh;
    max-width: 430px;
    margin: 0 auto;
    position: relative;
    overflow-x: hidden;
    padding-bottom: 80px;
  }

  /* NOISE TEXTURE */
  .app::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.3;
  }

  /* HEADER */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 12px;
    position: sticky;
    top: 0;
    z-index: 100;
    background: linear-gradient(180deg, var(--bg) 80%, transparent);
  }

  .logo {
    font-family: 'Bebas Neue', cursive;
    font-size: 28px;
    color: var(--lime);
    letter-spacing: 2px;
    line-height: 1;
  }

  .logo span { color: var(--text); }

  .balance-badge {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 14px;
    font-weight: 600;
    color: var(--lime);
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .avatar-btn {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 2px solid var(--lime);
    overflow: hidden;
    cursor: pointer;
    background: var(--surface2);
    flex-shrink: 0;
  }

  .avatar-btn img { width: 100%; height: 100%; object-fit: cover; }

  .avatar-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Bebas Neue', cursive;
    font-size: 16px;
    color: var(--lime);
  }

  /* SECTIONS */
  .section {
    padding: 0 16px;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
  }

  .section-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 22px;
    letter-spacing: 1.5px;
    color: var(--text);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  /* DAILY CARD */
  .daily-card {
    background: linear-gradient(135deg, #1A2A00 0%, var(--surface) 100%);
    border: 1px solid var(--lime);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    position: relative;
    overflow: hidden;
  }

  .daily-card::before {
    content: '';
    position: absolute;
    top: -20px; right: -20px;
    width: 100px; height: 100px;
    background: radial-gradient(circle, rgba(200,255,0,0.15) 0%, transparent 70%);
    pointer-events: none;
  }

  .daily-info h3 {
    font-family: 'Bebas Neue', cursive;
    font-size: 18px;
    color: var(--lime);
    letter-spacing: 1px;
  }

  .daily-info p {
    font-size: 12px;
    color: var(--muted);
    margin-top: 2px;
  }

  .daily-got {
    font-size: 12px;
    color: var(--muted);
    background: var(--surface2);
    padding: 6px 12px;
    border-radius: 20px;
  }

  /* CASES GRID */
  .cases-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .case-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
  }

  .case-card:active { transform: scale(0.97); }

  .case-card:hover { border-color: var(--lime); }

  .case-card::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: var(--case-color, var(--lime));
    opacity: 0.6;
  }

  .case-icon {
    font-size: 36px;
    margin-bottom: 8px;
    display: block;
    text-align: center;
  }

  .case-name {
    font-family: 'Bebas Neue', cursive;
    font-size: 15px;
    letter-spacing: 1px;
    text-align: center;
    margin-bottom: 6px;
  }

  .case-price {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: var(--lime);
  }

  /* COMING SOON */
  .coming-soon-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    position: relative;
    overflow: hidden;
  }

  .coming-soon-blur {
    font-size: 40px;
    filter: blur(8px);
    opacity: 0.5;
    user-select: none;
  }

  .coming-soon-label {
    font-family: 'Bebas Neue', cursive;
    font-size: 16px;
    letter-spacing: 2px;
    color: var(--muted);
  }

  /* BOTTOM NAV */
  .bottom-nav {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 430px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    display: flex;
    padding: 8px 16px 16px;
    z-index: 200;
  }

  .nav-btn {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 6px;
    border-radius: 8px;
    transition: background 0.15s;
    color: var(--muted);
    font-size: 10px;
    font-family: 'Inter', sans-serif;
  }

  .nav-btn.active { color: var(--lime); }
  .nav-btn:active { background: var(--surface2); }

  .nav-btn svg { width: 22px; height: 22px; }

  /* MODAL OVERLAY */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.85);
    z-index: 300;
    display: flex;
    align-items: flex-end;
    justify-content: center;
  }

  .modal {
    background: var(--surface);
    border-radius: 20px 20px 0 0;
    padding: 24px 20px 32px;
    width: 100%;
    max-width: 430px;
    max-height: 90vh;
    overflow-y: auto;
    border-top: 1px solid var(--border);
    animation: slideUp 0.3s ease;
  }

  @keyframes slideUp {
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
  }

  .modal-handle {
    width: 36px;
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    margin: 0 auto 20px;
  }

  .modal-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 24px;
    letter-spacing: 1.5px;
    margin-bottom: 16px;
    text-align: center;
  }

  /* BUTTONS */
  .btn {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }

  .btn:active { transform: scale(0.98); }

  .btn-primary {
    background: var(--lime);
    color: var(--bg);
  }

  .btn-secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
  }

  .btn-danger {
    background: rgba(255,68,68,0.15);
    color: var(--danger);
    border: 1px solid rgba(255,68,68,0.3);
  }

  .btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* INPUT */
  .input {
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 13px 14px;
    font-size: 15px;
    color: var(--text);
    font-family: 'Inter', sans-serif;
    outline: none;
    transition: border-color 0.15s;
  }

  .input:focus { border-color: var(--lime); }
  .input::placeholder { color: var(--muted); }

  .input-label {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 6px;
    font-weight: 500;
  }

  .input-group {
    margin-bottom: 14px;
  }

  /* SPIN ANIMATION */
  .spin-container {
    overflow: hidden;
    border: 2px solid var(--lime);
    border-radius: 12px;
    position: relative;
    margin-bottom: 20px;
    height: 100px;
  }

  .spin-track {
    display: flex;
    gap: 8px;
    padding: 8px;
    transition: transform 6s cubic-bezier(0.17, 0.67, 0.12, 0.99);
    will-change: transform;
  }

  .spin-item {
    min-width: 80px;
    height: 84px;
    border-radius: 8px;
    background: var(--surface2);
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    flex-shrink: 0;
    font-size: 11px;
    text-align: center;
    padding: 6px;
  }

  .spin-item .spin-stars {
    font-size: 14px;
    font-weight: 700;
    color: var(--lime);
  }

  .spin-pointer {
    position: absolute;
    top: 0; bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    background: var(--lime);
    z-index: 10;
  }

  .spin-pointer::before {
    content: '▼';
    position: absolute;
    top: -2px;
    left: 50%;
    transform: translateX(-50%);
    color: var(--lime);
    font-size: 10px;
  }

  /* WIN RESULT */
  .win-result {
    text-align: center;
    padding: 20px 0;
  }

  .win-stars {
    font-family: 'Bebas Neue', cursive;
    font-size: 52px;
    color: var(--lime);
    line-height: 1;
  }

  .win-label {
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
    margin-bottom: 16px;
  }

  .rarity-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    border: 1px solid;
  }

  /* PROFILE */
  .profile-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 24px 0 16px;
  }

  .profile-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 3px solid var(--lime);
    overflow: hidden;
    background: var(--surface2);
  }

  .profile-avatar img { width: 100%; height: 100%; object-fit: cover; }

  .profile-name {
    font-family: 'Bebas Neue', cursive;
    font-size: 22px;
    letter-spacing: 1px;
  }

  .profile-username {
    font-size: 13px;
    color: var(--muted);
    margin-top: -6px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    margin-bottom: 20px;
  }

  .stat-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 8px;
    text-align: center;
  }

  .stat-value {
    font-family: 'Bebas Neue', cursive;
    font-size: 22px;
    color: var(--lime);
  }

  .stat-label {
    font-size: 10px;
    color: var(--muted);
    margin-top: 2px;
  }

  /* HISTORY */
  .history-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
  }

  .history-item:last-child { border-bottom: none; }

  .history-left { display: flex; flex-direction: column; gap: 2px; }
  .history-case { font-size: 13px; font-weight: 500; }
  .history-date { font-size: 11px; color: var(--muted); }
  .history-stars { font-size: 14px; font-weight: 700; color: var(--lime); }

  /* WALLET */
  .wallet-balance {
    background: linear-gradient(135deg, #1A2A00, #0F1A00);
    border: 1px solid var(--lime);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
  }

  .wallet-balance-label {
    font-size: 12px;
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .wallet-balance-amount {
    font-family: 'Bebas Neue', cursive;
    font-size: 48px;
    color: var(--lime);
    line-height: 1;
    margin: 4px 0;
  }

  .wallet-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 20px;
  }

  /* ADMIN */
  .admin-header {
    background: linear-gradient(135deg, #2A0000, #1A0000);
    border: 1px solid rgba(255,68,68,0.4);
    border-radius: 12px;
    padding: 14px;
    text-align: center;
    margin-bottom: 16px;
  }

  .admin-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 20px;
    color: #FF6666;
    letter-spacing: 2px;
  }

  .user-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background: var(--surface2);
    border-radius: 8px;
    margin-bottom: 6px;
    border: 1px solid var(--border);
  }

  .user-row-left { display: flex; flex-direction: column; gap: 2px; }
  .user-row-name { font-size: 13px; font-weight: 500; }
  .user-row-id { font-size: 11px; color: var(--muted); }
  .user-row-balance { font-size: 14px; font-weight: 700; color: var(--lime); }

  /* SUBSCRIBE GATE */
  .subscribe-gate {
    text-align: center;
    padding: 16px 0;
  }

  .subscribe-gate p {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 14px;
    line-height: 1.5;
  }

  .subscribe-channels {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }

  .channel-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
  }

  .check-icon { color: var(--lime); }
  .x-icon { color: var(--danger); }

  .toast {
    position: fixed;
    bottom: 90px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 13px;
    z-index: 500;
    animation: fadeInOut 2.5s ease forwards;
    white-space: nowrap;
  }

  @keyframes fadeInOut {
    0% { opacity: 0; transform: translateX(-50%) translateY(10px); }
    15% { opacity: 1; transform: translateX(-50%) translateY(0); }
    70% { opacity: 1; }
    100% { opacity: 0; }
  }

  .error-text {
    color: var(--danger);
    font-size: 13px;
    text-align: center;
    margin-top: 8px;
  }

  .success-text {
    color: var(--lime);
    font-size: 13px;
    text-align: center;
    margin-top: 8px;
  }

  .divider {
    height: 1px;
    background: var(--border);
    margin: 16px 0;
  }

  .quick-amounts {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }

  .quick-amount {
    padding: 6px 14px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    color: var(--text);
    transition: border-color 0.15s;
  }

  .quick-amount:hover, .quick-amount.active {
    border-color: var(--lime);
    color: var(--lime);
  }
`;

// ============================================================
// COMPONENTS
// ============================================================

function StarIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

function WalletIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <path d="M16 14a1 1 0 100-2 1 1 0 000 2z" fill="currentColor" />
      <path d="M2 10h20" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function GiftIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="8" width="18" height="13" rx="1.5" />
      <path d="M3 12h18" />
      <path d="M12 8v13" />
      <path d="M12 8c-1.5-3-3-4.5-4.5-4.5S5 4.8 5 6.25 6.5 8 8 8" />
      <path d="M12 8c1.5-3 3-4.5 4.5-4.5S19 4.8 19 6.25 17.5 8 16 8" />
    </svg>
  );
}

function CrownIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 18h18" />
      <path d="M4 18l-1-9 5 4 4-7 4 7 5-4-1 9" />
    </svg>
  );
}

function DiceIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <circle cx="8" cy="8" r="1" fill="currentColor" />
      <circle cx="16" cy="8" r="1" fill="currentColor" />
      <circle cx="8" cy="16" r="1" fill="currentColor" />
      <circle cx="16" cy="16" r="1" fill="currentColor" />
      <circle cx="12" cy="12" r="1" fill="currentColor" />
    </svg>
  );
}

function ChatIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
    </svg>
  );
}

function MegaphoneIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 11v3a1 1 0 001 1h1l4 4V6L5 10H4a1 1 0 00-1 1z" />
      <path d="M14 8a3 3 0 010 8" />
      <path d="M18 5a7 7 0 010 14" />
    </svg>
  );
}

function ChevronRightIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function ArrowUpIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="19" x2="12" y2="5" />
      <polyline points="5 12 12 5 19 12" />
    </svg>
  );
}

function PlusIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

function TrophyIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 21h8" />
      <path d="M12 17v4" />
      <path d="M7 4h10v5a5 5 0 01-10 0V4z" />
      <path d="M7 5H4a2 2 0 002 4" />
      <path d="M17 5h3a2 2 0 01-2 4" />
    </svg>
  );
}

function SparkleIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3z" />
    </svg>
  );
}

function LockIcon({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="11" width="16" height="9" rx="2" />
      <path d="M8 11V7a4 4 0 018 0v4" />
    </svg>
  );
}

function CheckIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function BoxIcon({ size = 32, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16V8z" />
      <path d="M3.27 6.96L12 12l8.73-5.04" />
      <path d="M12 22.08V12" />
    </svg>
  );
}

function MedalIcon({ size = 32, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="14" r="6" />
      <path d="M9 10.5L7 3h2l3 4 3-4h2l-2 7.5" />
      <path d="M10 14l2 2 3-3" />
    </svg>
  );
}

function CaseIcon({ color }) {
  return (
    <svg width="36" height="36" viewBox="0 0 48 48" fill="none">
      <rect x="4" y="16" width="40" height="28" rx="3" fill={color} opacity="0.15" />
      <rect x="4" y="16" width="40" height="28" rx="3" stroke={color} strokeWidth="2" />
      <rect x="14" y="10" width="20" height="8" rx="2" fill={color} opacity="0.3" stroke={color} strokeWidth="2" />
      <line x1="4" y1="28" x2="44" y2="28" stroke={color} strokeWidth="1.5" opacity="0.5" />
      <rect x="20" y="24" width="8" height="8" rx="1" fill={color} opacity="0.8" />
    </svg>
  );
}

function Toast({ msg }) {
  return <div className="toast">{msg}</div>;
}

// ============================================================
// CASE OPEN MODAL
// ============================================================
function CaseOpenModal({ caseType, caseData, user, onClose, onUpdate }) {
  const [phase, setPhase] = useState("subscribe"); // subscribe | confirm | spinning | result
  const [subscribed, setSubscribed] = useState({ channel: false, chat: false });
  const [checking, setChecking] = useState(false);
  const [spinning, setSpinning] = useState(false);
  const [spinItems, setSpinItems] = useState([]);
  const [trackOffset, setTrackOffset] = useState(0);
  const [wonItem, setWonItem] = useState(null);
  const [error, setError] = useState("");

  const isDaily = caseType === "daily";
  const alreadyGot = isDaily && user?.last_daily === new Date().toISOString().slice(0, 10);

  useEffect(() => {
    if (alreadyGot) setPhase("got");
    else if (!isDaily) setPhase("confirm");
    else setPhase("subscribe");
  }, []);

  function openTgLink(url) {
    if (window.Telegram?.WebApp?.openTelegramLink) {
      window.Telegram.WebApp.openTelegramLink(url);
    } else {
      window.open(url, "_blank");
    }
  }

  async function checkSubs() {
    setChecking(true);
    setTimeout(() => {
      setSubscribed({ channel: true, chat: true });
      setChecking(false);
    }, 1500);
  }

  async function doOpen() {
    setError("");
    setPhase("spinning");
    try {
      const res = await api(`/api/cases/${caseType}/open`, { method: "POST", body: {} });
      // Build spin track
      const items = res.spin_items;
      setSpinItems(items);
      setWonItem(res.won);

      // Calculate offset to land on last item (won)
      const itemW = 88; // 80px + 8px gap
      const center = Math.floor(window.innerWidth / 2);
      const target = (items.length - 1) * itemW + itemW / 2;
      const offset = -(target - center + 100);
      
      setTimeout(() => {
        setTrackOffset(offset);
        setTimeout(() => {
          setPhase("result");
          onUpdate(res.new_balance);
        }, 6500);
      }, 100);
    } catch (e) {
      setError(e.message);
      setPhase(isDaily ? "subscribe" : "confirm");
    }
  }

  const rarityColor = wonItem ? RARITY_COLORS[wonItem.rarity] : "#C8FF00";

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-handle" />
        
        {phase === "got" && (
          <>
            <div className="modal-title" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
              Уже получено <CheckIcon size={18} />
            </div>
            <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 13, marginBottom: 20 }}>
              Ежедневный кейс уже открыт сегодня.<br />Возвращайся завтра!
            </p>
            <button className="btn btn-secondary" onClick={onClose}>Закрыть</button>
          </>
        )}

        {phase === "subscribe" && (
          <>
            <div className="modal-title" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
              <GiftIcon size={22} /> Бесплатный кейс
            </div>
            <div className="subscribe-gate">
              <p>Подпишись на наш канал и чат, чтобы получить ежедневный кейс бесплатно</p>
              <div className="subscribe-channels">
                <button className="channel-btn" onClick={() => openTgLink("https://t.me/justgif_t")}>
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}><MegaphoneIcon size={16} /> Канал @justgif_t</span>
                  {subscribed.channel && <span className="check-icon"><CheckIcon /></span>}
                </button>
                <button className="channel-btn" onClick={() => openTgLink("https://t.me/justgiftchat")}>
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}><ChatIcon size={16} /> Чат @justgiftchat</span>
                  {subscribed.chat && <span className="check-icon"><CheckIcon /></span>}
                </button>
              </div>
              {!subscribed.channel && (
                <button className="btn btn-secondary" style={{ marginBottom: 10 }} onClick={checkSubs} disabled={checking}>
                  {checking ? "Проверяю..." : "Проверить подписку"}
                </button>
              )}
              {subscribed.channel && subscribed.chat && (
                <button className="btn btn-primary" onClick={doOpen} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                  <DiceIcon size={18} /> Открыть кейс!
                </button>
              )}
            </div>
          </>
        )}

        {phase === "confirm" && (
          <>
            <div className="modal-title">{caseData.name}</div>
            <div style={{ textAlign: "center", marginBottom: 20 }}>
              <div style={{ marginBottom: 12 }}>
                <CaseIcon color={caseData.color} />
              </div>
              <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>Возможные награды:</div>
              {caseData.items.map((item, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "5px 12px", background: i % 2 === 0 ? "var(--surface2)" : "transparent", borderRadius: 6, fontSize: 13 }}>
                  <span style={{ color: RARITY_COLORS[item.rarity] }}>{RARITY_LABELS[item.rarity]}</span>
                  <span>{item.name}</span>
                  <span style={{ color: "var(--muted)" }}>{item.chance}%</span>
                </div>
              ))}
            </div>
            {error && <div className="error-text">{error}</div>}
            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
              <button className="btn btn-primary" onClick={doOpen}>
                <StarIcon /> Открыть за {caseData.price}
              </button>
              <button className="btn btn-secondary" onClick={onClose}>Отмена</button>
            </div>
          </>
        )}

        {phase === "spinning" && (
          <>
            <div className="modal-title" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
              <DiceIcon size={22} /> Крутим...
            </div>
            <div className="spin-container">
              <div className="spin-pointer" />
              <div
                className="spin-track"
                style={{ transform: `translateX(${trackOffset}px)` }}
              >
                {spinItems.map((item, i) => (
                  <div key={i} className="spin-item" style={{ borderColor: RARITY_COLORS[item.rarity] }}>
                    <StarIcon size={14} />
                    <div className="spin-stars">{item.stars}</div>
                    <div style={{ fontSize: 9, color: RARITY_COLORS[item.rarity] }}>{RARITY_LABELS[item.rarity]}</div>
                  </div>
                ))}
              </div>
            </div>
            <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 13 }}>Удача на твоей стороне...</p>
          </>
        )}

        {phase === "result" && wonItem && (
          <>
            <div className="modal-title" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
              <SparkleIcon size={22} /> Выигрыш!
            </div>
            <div className="win-result">
              <div style={{ marginBottom: 8, color: rarityColor, display: "flex", justifyContent: "center" }}>
                <StarIcon size={40} />
              </div>
              <div className="win-stars">{wonItem.stars}</div>
              <div className="win-label">звёзд зачислено на баланс</div>
              <span className="rarity-badge" style={{ color: rarityColor, borderColor: rarityColor }}>
                {RARITY_LABELS[wonItem.rarity]}
              </span>
            </div>
            <button className="btn btn-primary" onClick={onClose} style={{ marginTop: 16 }}>
              Отлично!
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================
// WALLET MODAL
// ============================================================
function WalletModal({ user, onClose, onUpdate }) {
  const [tab, setTab] = useState("deposit"); // deposit | withdraw
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const quickAmounts = [50, 100, 250, 500, 1000];

  async function handleDeposit() {
    setLoading(true);
    setError("");
    try {
      const res = await api("/api/deposit/request", { method: "POST", body: { amount: parseInt(amount) } });
      setResult({ type: "deposit", url: res.bot_url, amount: res.amount });
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  async function handleWithdraw() {
    setLoading(true);
    setError("");
    try {
      const res = await api("/api/withdraw/request", { method: "POST", body: { amount: parseInt(amount) } });
      setResult({ type: "withdraw", url: res.bot_url, amount: res.amount });
      onUpdate(user.balance - res.amount);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  function openBot(url) {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openTelegramLink(url);
    } else {
      window.open(url, "_blank");
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-handle" />
        
        <div className="wallet-balance">
          <div className="wallet-balance-label">Баланс</div>
          <div className="wallet-balance-amount">{user?.balance || 0}</div>
          <div style={{ color: "var(--muted)", fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
            <StarIcon size={13} /> звёзд
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {["deposit", "withdraw"].map(t => (
            <button key={t} className={`btn ${tab === t ? "btn-primary" : "btn-secondary"}`}
              style={{ flex: 1 }} onClick={() => { setTab(t); setResult(null); setError(""); }}>
              {t === "deposit" ? "Пополнить" : "Вывести"}
            </button>
          ))}
        </div>

        {!result ? (
          <>
            <div className="input-group">
              <div className="input-label">{tab === "deposit" ? "Сумма пополнения" : "Сумма вывода (мин. 50)"}</div>
              <input className="input" type="number" placeholder="100" value={amount}
                onChange={e => setAmount(e.target.value)} />
            </div>
            <div className="quick-amounts">
              {quickAmounts.map(a => (
                <button key={a} className={`quick-amount ${parseInt(amount) === a ? "active" : ""}`}
                  onClick={() => setAmount(String(a))}>
                  {a}
                </button>
              ))}
            </div>
            {error && <div className="error-text">{error}</div>}
            <button className="btn btn-primary" disabled={!amount || loading}
              onClick={tab === "deposit" ? handleDeposit : handleWithdraw}>
              {loading ? "Обработка..." : tab === "deposit" ? `Пополнить ${amount || "..."}` : `Вывести ${amount || "..."}`}
            </button>
          </>
        ) : (
          <div style={{ textAlign: "center" }}>
            <div style={{ marginBottom: 8, color: "var(--lime)", display: "flex", justifyContent: "center" }}>
              {result.type === "deposit" ? <PlusIcon size={40} /> : <ArrowUpIcon size={40} />}
            </div>
            <div style={{ fontFamily: "'Bebas Neue', cursive", fontSize: 20, marginBottom: 8, letterSpacing: 1 }}>
              {result.type === "deposit" ? "Перейди в бот для оплаты" : "Запрос принят"}
            </div>
            <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 16, lineHeight: 1.5 }}>
              {result.type === "deposit"
                ? `Бот пришлёт счёт на ${result.amount} для оплаты`
                : `Вывод ${result.amount} будет обработан в течение 24 часов`}
            </p>
            <button className="btn btn-primary" style={{ marginBottom: 8 }} onClick={() => openBot(result.url)}>
              Открыть бот →
            </button>
            <button className="btn btn-secondary" onClick={onClose}>Закрыть</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// PROFILE PAGE
// ============================================================
function ProfilePage({ user, onOpenWallet }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api("/api/history").then(setHistory).catch(() => {});
  }, []);

  const name = user?.first_name || "Игрок";
  const username = user?.username ? `@${user.username}` : `ID: ${user?.tg_id}`;

  return (
    <div className="section">
      <div className="profile-header">
        <div className="profile-avatar">
          {user?.photo_url
            ? <img src={user.photo_url} alt="" />
            : <div className="avatar-placeholder" style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Bebas Neue', cursive", fontSize: 28, color: "var(--lime)" }}>
                {name[0]?.toUpperCase()}
              </div>
          }
        </div>
        <div className="profile-name">{name}</div>
        <div className="profile-username">{username}</div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{user?.balance || 0}</div>
          <div className="stat-label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}><StarIcon size={11} /> Баланс</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{user?.cases_opened || 0}</div>
          <div className="stat-label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}><BoxIcon size={11} /> Кейсов</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{user?.total_won || 0}</div>
          <div className="stat-label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}><TrophyIcon size={11} /> Выиграно</div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
        <button className="btn btn-primary" onClick={onOpenWallet} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <WalletIcon /> Кошелёк
        </button>
      </div>

      {history.length > 0 && (
        <>
          <div className="section-title">История</div>
          {history.map((h, i) => (
            <div key={i} className="history-item">
              <div className="history-left">
                <div className="history-case">{h.item_name}</div>
                <div className="history-date">{new Date(h.created_at).toLocaleDateString("ru-RU")}</div>
              </div>
              <div>
                <span className="history-stars" style={{ display: "flex", alignItems: "center", gap: 4 }}>+{h.stars_won} <StarIcon size={12} /></span>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

// ============================================================
// ADMIN PAGE
// ============================================================
function AdminPage({ user }) {
  const [users, setUsers] = useState([]);
  const [targetId, setTargetId] = useState("");
  const [giveAmount, setGiveAmount] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api("/api/admin/users").then(setUsers).catch(() => {});
  }, []);

  async function giveStars() {
    setLoading(true);
    setError(""); setMsg("");
    try {
      const res = await api("/api/admin/give-stars", {
        method: "POST",
        body: { tg_id: parseInt(targetId), amount: parseInt(giveAmount) }
      });
      setMsg(res.message);
      setUsers(u => u.map(x => x.tg_id === parseInt(targetId) ? { ...x, balance: x.balance + parseInt(giveAmount) } : x));
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  return (
    <div className="section">
      <div className="admin-header">
        <div className="admin-title" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <CrownIcon size={20} /> Панель администратора
        </div>
      </div>

      <div className="section-title">Выдать звёзды</div>
      <div className="input-group">
        <div className="input-label">Telegram ID пользователя</div>
        <input className="input" placeholder="123456789" value={targetId} onChange={e => setTargetId(e.target.value)} />
      </div>
      <div className="input-group">
        <div className="input-label">Количество звёзд</div>
        <input className="input" type="number" placeholder="100" value={giveAmount} onChange={e => setGiveAmount(e.target.value)} />
      </div>
      {error && <div className="error-text">{error}</div>}
      {msg && <div className="success-text">{msg}</div>}
      <button className="btn btn-primary" disabled={!targetId || !giveAmount || loading} onClick={giveStars} style={{ marginBottom: 20, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
        {loading ? "Выдаю..." : <><StarIcon size={16} /> Выдать звёзды</>}
      </button>

      <div className="section-title">Пользователи</div>
      {users.map(u => (
        <div key={u.tg_id} className="user-row" onClick={() => setTargetId(String(u.tg_id))}>
          <div className="user-row-left">
            <div className="user-row-name">{u.first_name || "—"} {u.username ? `@${u.username}` : ""}</div>
            <div className="user-row-id">ID: {u.tg_id}</div>
          </div>
          <div className="user-row-balance" style={{ display: "flex", alignItems: "center", gap: 4 }}>{u.balance} <StarIcon size={12} /></div>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// MAIN APP
// ============================================================
export default function App() {
  const [user, setUser] = useState(null);
  const [cases, setCases] = useState({});
  const [tab, setTab] = useState("home");
  const [openingCase, setOpeningCase] = useState(null);
  const [showWallet, setShowWallet] = useState(false);
  const [toast, setToast] = useState("");

  const isAdmin = user?.tg_id === 8526401545;

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 2500);
  }

  useEffect(() => {
    // Init Telegram WebApp
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }

    api("/api/me").then(setUser).catch(console.error);
    api("/api/cases").then(setCases).catch(console.error);
  }, []);

  function updateBalance(newBalance) {
    setUser(u => ({ ...u, balance: newBalance }));
  }

  const caseList = [
    { key: "bronze", Icon: BoxIcon, label: "Бронзовый" },
    { key: "silver", Icon: MedalIcon, label: "Серебряный" },
    { key: "gold", Icon: CrownIcon, label: "Золотой" },
  ];

  const today = new Date().toISOString().slice(0, 10);
  const dailyGot = user?.last_daily === today;

  return (
    <>
      <style>{styles}</style>
      <div className="app">
        {/* HEADER */}
        <div className="header">
          <div className="logo">Just<span>gift</span></div>
          <div className="balance-badge">
            <StarIcon size={13} /> {user?.balance ?? "—"}
          </div>
          <button className="avatar-btn" onClick={() => setTab("profile")}>
            {user?.photo_url
              ? <img src={user.photo_url} alt="" />
              : <div className="avatar-placeholder">{user?.first_name?.[0]?.toUpperCase() || "?"}</div>
            }
          </button>
        </div>

        {/* HOME TAB */}
        {tab === "home" && (
          <>
            {/* Daily case */}
            <div className="section">
              <div className="section-title">Бесплатно</div>
              <div className="daily-card" onClick={() => !dailyGot && setOpeningCase("daily")}
                style={{ cursor: dailyGot ? "default" : "pointer" }}>
                <div className="daily-info">
                  <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}><GiftIcon size={18} /> Ежедневный кейс</h3>
                  <p>Подпишись на канал и получи награду</p>
                </div>
                {dailyGot
                  ? <div className="daily-got" style={{ display: "flex", alignItems: "center", gap: 6 }}>Уже получен <CheckIcon size={13} /></div>
                  : <button className="btn btn-primary" style={{ width: "auto", padding: "8px 16px", fontSize: 13 }}
                      onClick={() => setOpeningCase("daily")}>Взять</button>
                }
              </div>
            </div>

            {/* Cases */}
            <div className="section">
              <div className="section-title">Кейсы</div>
              <div className="cases-grid">
                {caseList.map(({ key, Icon, label }) => {
                  const c = cases[key];
                  if (!c) return null;
                  return (
                    <div key={key} className="case-card"
                      style={{ "--case-color": c.color }}
                      onClick={() => setOpeningCase(key)}>
                      <span className="case-icon" style={{ display: "flex", justifyContent: "center", color: c.color }}><Icon size={36} /></span>
                      <div className="case-name">{label}</div>
                      <div className="case-price"><StarIcon size={11} /> {c.price}</div>
                    </div>
                  );
                })}

                {/* Coming soon — blurred game slot */}
                <div className="coming-soon-card">
                  <div className="coming-soon-blur"><DiceIcon size={40} /></div>
                  <div className="coming-soon-label">Скоро новая игра...</div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* WALLET TAB */}
        {tab === "wallet" && (
          <div className="section" style={{ paddingTop: 8 }}>
            <div className="section-title">Кошелёк</div>
            <div className="wallet-balance">
              <div className="wallet-balance-label">Текущий баланс</div>
              <div className="wallet-balance-amount">{user?.balance || 0}</div>
              <div style={{ color: "var(--muted)", fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                <StarIcon size={13} /> звёзд
              </div>
            </div>
            <div className="wallet-actions">
              <button className="btn btn-primary" onClick={() => setShowWallet(true)} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <PlusIcon size={16} /> Пополнить
              </button>
              <button className="btn btn-secondary" onClick={() => setShowWallet(true)} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <ArrowUpIcon size={16} /> Вывести
              </button>
            </div>

            <div className="section-title">Статистика</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{user?.balance || 0}</div>
                <div className="stat-label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}><StarIcon size={11} /> Баланс</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{user?.cases_opened || 0}</div>
                <div className="stat-label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}><BoxIcon size={11} /> Кейсов</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{user?.total_won || 0}</div>
                <div className="stat-label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}><TrophyIcon size={11} /> Выиграно</div>
              </div>
            </div>
          </div>
        )}

        {/* PROFILE TAB */}
        {tab === "profile" && (
          <ProfilePage user={user} onOpenWallet={() => setShowWallet(true)} />
        )}

        {/* ADMIN TAB */}
        {tab === "admin" && isAdmin && (
          <AdminPage user={user} />
        )}

        {/* BOTTOM NAV */}
        <div className="bottom-nav">
          <button className={`nav-btn ${tab === "home" ? "active" : ""}`} onClick={() => setTab("home")}>
            <HomeIcon /> Главная
          </button>
          <button className={`nav-btn ${tab === "wallet" ? "active" : ""}`} onClick={() => setTab("wallet")}>
            <WalletIcon /> Кошелёк
          </button>
          <button className={`nav-btn ${tab === "profile" ? "active" : ""}`} onClick={() => setTab("profile")}>
            <UserIcon /> Профиль
          </button>
          {isAdmin && (
            <button className={`nav-btn ${tab === "admin" ? "active" : ""}`} onClick={() => setTab("admin")}>
              <ShieldIcon /> Админ
            </button>
          )}
        </div>

        {/* MODALS */}
        {openingCase && cases[openingCase] && (
          <CaseOpenModal
            caseType={openingCase}
            caseData={cases[openingCase]}
            user={user}
            onClose={() => setOpeningCase(null)}
            onUpdate={(bal) => {
              updateBalance(bal);
              setUser(u => ({ ...u, cases_opened: (u.cases_opened || 0) + 1 }));
              showToast("Кейс открыт!");
            }}
          />
        )}

        {showWallet && (
          <WalletModal
            user={user}
            onClose={() => setShowWallet(false)}
            onUpdate={updateBalance}
          />
        )}

        {toast && <Toast msg={toast} />}
      </div>
    </>
  );
    }
