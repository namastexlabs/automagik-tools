// ===================================================================
// Automagik Tools Hub - PM2 Configuration
// ===================================================================
// Multi-tenant Hub server with WorkOS authentication and auto-migration
const path = require('path');
const fs = require('fs');

// Get the current directory (automagik-tools)
const PROJECT_ROOT = __dirname;

/**
 * Extract version from pyproject.toml file
 * @param {string} projectPath - Path to the project directory
 * @returns {string} Version string or 'unknown'
 */
function extractVersionFromPyproject(projectPath) {
  const pyprojectPath = path.join(projectPath, 'pyproject.toml');

  if (!fs.existsSync(pyprojectPath)) {
    return 'unknown';
  }

  try {
    const content = fs.readFileSync(pyprojectPath, 'utf8');

    // Standard approach: Static version in [project] section
    const projectVersionMatch = content.match(/\[project\][\s\S]*?version\s*=\s*["']([^"']+)["']/);
    if (projectVersionMatch) {
      return projectVersionMatch[1];
    }

    // Fallback: Simple version = "..." pattern anywhere in file
    const simpleVersionMatch = content.match(/^version\s*=\s*["']([^"']+)["']/m);
    if (simpleVersionMatch) {
      return simpleVersionMatch[1];
    }

    return 'unknown';
  } catch (error) {
    console.warn(`Failed to read version from ${pyprojectPath}:`, error.message);
    return 'unknown';
  }
}

// Load environment variables from .env file if it exists
const envPath = path.join(PROJECT_ROOT, '.env');
let envVars = {};
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    // Skip comments and empty lines
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;

    const eqIndex = line.indexOf('=');
    if (eqIndex > 0) {
      const key = line.substring(0, eqIndex).trim();
      const value = line.substring(eqIndex + 1).trim().replace(/^["']|["']$/g, '');
      envVars[key] = value;
    }
  });
}

// Create logs directory if it doesn't exist
const logsDir = path.join(PROJECT_ROOT, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Create data directory for database (new default location)
const dataDir = path.join(PROJECT_ROOT, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const version = extractVersionFromPyproject(PROJECT_ROOT);

module.exports = {
  apps: [
    // ===================================================================
    // Tools Hub - HTTP Server with Database-First Configuration
    // ===================================================================
    // Uses Python startup wrapper that reads port/host from database.
    // This enables zero-configuration: database is the only source of truth.
    // Port/host no longer need to be set in .env after initial setup.
    {
      name: '8000-automagik-tools',
      cwd: PROJECT_ROOT,
      script: path.join(PROJECT_ROOT, '.venv/bin/python'),
      args: '-m automagik_tools.hub.start',
      interpreter: 'none',
      version: version,
      env: {
        ...envVars,
        PYTHONPATH: PROJECT_ROOT,
        // Database path is still read from .env for bootstrap, but host/port come from DB
        HUB_DATABASE_PATH: envVars.HUB_DATABASE_PATH || './data/hub.db',
        NODE_ENV: 'production',
        PROCESS_TITLE: 'Tools Hub'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 2000,
      kill_timeout: 10000,
      error_file: path.join(PROJECT_ROOT, 'logs/hub-err.log'),
      out_file: path.join(PROJECT_ROOT, 'logs/hub-out.log'),
      log_file: path.join(PROJECT_ROOT, 'logs/hub-combined.log'),
      merge_logs: true,
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ],

  // ===================================================================
  // PM2 Deploy Configuration (Optional)
  // ===================================================================
  deploy: {
    production: {
      user: 'deploy',
      host: 'your-server.com',
      ref: 'origin/main',
      repo: 'git@github.com:namastex-labs/automagik-tools.git',
      path: '/var/www/automagik-tools',
      'pre-deploy-local': '',
      'post-deploy': 'uv sync && .venv/bin/alembic upgrade head && pm2 reload ecosystem.config.js --env production',
      'pre-setup': '',
      env: {
        NODE_ENV: 'production'
      }
    }
  }
};