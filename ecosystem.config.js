// ===================================================================
// 🛠️ Automagik-Tools - PM2 Configuration for Two Services
// ===================================================================
// This file creates two separate PM2 services:
// - automagik-tools-sse (port 8884)
// - automagik-tools-http (port 8885)

const path = require('path');
const fs = require('fs');

// Get the current directory (automagik-tools)
const PROJECT_ROOT = __dirname;

/**
 * Extract version from pyproject.toml file using standardized approach
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
    const [key, value] = line.split('=');
    if (key && value) {
      envVars[key.trim()] = value.trim().replace(/^["']|["']$/g, '');
    }
  });
}

module.exports = {
  apps: [
    {
      name: 'automagik-tools-sse',
      cwd: PROJECT_ROOT,
      script: '.venv/bin/automagik-tools',
      args: 'hub --host 0.0.0.0 --port ' + (envVars.PORT || '8884') + ' --transport sse',
      interpreter: 'none',
      version: extractVersionFromPyproject(PROJECT_ROOT),
      env: {
        ...envVars,
        PYTHONPATH: PROJECT_ROOT,
        PORT: envVars.PORT || '8884',
        HOST: envVars.HOST || '0.0.0.0',
        NODE_ENV: 'production'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 1000,
      kill_timeout: 5000,
      error_file: path.join(PROJECT_ROOT, 'logs/sse-err.log'),
      out_file: path.join(PROJECT_ROOT, 'logs/sse-out.log'),
      log_file: path.join(PROJECT_ROOT, 'logs/sse-combined.log'),
      merge_logs: true,
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'automagik-tools-http',
      cwd: PROJECT_ROOT,
      script: '.venv/bin/automagik-tools',
      args: 'hub --host 0.0.0.0 --port ' + (envVars.AUTOMAGIK_TOOLS_PORT || '8885') + ' --transport http',
      interpreter: 'none',
      version: extractVersionFromPyproject(PROJECT_ROOT),
      env: {
        ...envVars,
        PYTHONPATH: PROJECT_ROOT,
        PORT: envVars.AUTOMAGIK_TOOLS_PORT || '8885',
        AUTOMAGIK_TOOLS_PORT: envVars.AUTOMAGIK_TOOLS_PORT || '8885',
        HOST: envVars.HOST || '0.0.0.0',
        NODE_ENV: 'production'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 1000,
      kill_timeout: 5000,
      error_file: path.join(PROJECT_ROOT, 'logs/http-err.log'),
      out_file: path.join(PROJECT_ROOT, 'logs/http-out.log'),
      log_file: path.join(PROJECT_ROOT, 'logs/http-combined.log'),
      merge_logs: true,
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};