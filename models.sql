PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  is_active INTEGER DEFAULT 0,
  balance_points INTEGER DEFAULT 0,
  total_tasks_completed INTEGER DEFAULT 0,
  total_referrals_active INTEGER DEFAULT 0,
  withdraw_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activation_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  method TEXT CHECK(method IN ('bkash','nagad')) NOT NULL,
  amount INTEGER NOT NULL,
  trx_id TEXT NOT NULL,
  status TEXT CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- used trx store (never delete)
CREATE TABLE IF NOT EXISTS used_transactions (
  trx_id TEXT PRIMARY KEY,
  used_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  link TEXT,
  points INTEGER NOT NULL,
  screenshot_required INTEGER DEFAULT 0,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  task_id INTEGER NOT NULL,
  status TEXT CHECK(status IN ('pending','submitted','approved')) DEFAULT 'pending',
  screenshot_submitted INTEGER DEFAULT 0, -- no file, just flag
  submitted_at TEXT,
  UNIQUE(user_id, task_id)
);

CREATE TABLE IF NOT EXISTS withdraw_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  amount_points INTEGER NOT NULL,
  method TEXT CHECK(method IN ('bkash','nagad')) NOT NULL,
  number TEXT NOT NULL,
  status TEXT CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- deep-link referral: pending until activate
CREATE TABLE IF NOT EXISTS pending_referrals (
  user_id INTEGER PRIMARY KEY,           -- who came
  referrer_id INTEGER NOT NULL,          -- who invited
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- confirmed referrals (with staged bonuses)
CREATE TABLE IF NOT EXISTS referrals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  referrer_id INTEGER NOT NULL,
  referred_user_id INTEGER NOT NULL,
  started_at TEXT DEFAULT CURRENT_TIMESTAMP, -- when referral activated
  months_paid INTEGER DEFAULT 0,             -- how many monthly bonuses paid (0..11)
  expires_at TEXT NOT NULL,                  -- started_at + 12 months
  UNIQUE(referrer_id, referred_user_id)
);

-- configurable settings
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- daily stats snapshot
CREATE TABLE IF NOT EXISTS daily_stats (
  stat_date TEXT PRIMARY KEY,
  tasks_completed INTEGER DEFAULT 0,
  points_distributed INTEGER DEFAULT 0,
  new_registrations INTEGER DEFAULT 0,
  withdraw_requests INTEGER DEFAULT 0,
  active_users INTEGER DEFAULT 0,
  inactive_users INTEGER DEFAULT 0,
  total_withdraw_points INTEGER DEFAULT 0
);
