/**
 * PM2 Ecosystem Configuration for automagik-tools
 *
 * Foundation for running your own MCP tool server powerhouse.
 * Each tool runs as an independent PM2 process in HTTP/SSE mode.
 *
 * Port Allocation Strategy:
 * - 11000-11099: Production MCP tools (OAuth, Google Workspace, core tools)
 * - Auto-restart, memory limits, log rotation built-in
 *
 * Usage:
 *   pm2 start ecosystem.config.cjs                    # Start all tools
 *   pm2 start ecosystem.config.cjs --only oauth       # Start specific tool
 *   pm2 logs google-calendar                          # View logs
 *   pm2 monit                                         # Monitor all processes
 *   pm2 restart all                                   # Restart all tools
 *
 * Leave a trail for fellow friends to follow! 🚀
 */

module.exports = {
  apps: [
    // ============================================================================
    // OAUTH & AUTHENTICATION - Port 11000-11001
    // ============================================================================

    {
      name: 'oauth',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.namastex_oauth_server --transport sse --host 0.0.0.0 --port 11000',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        OAUTH_SERVER_PORT: '11000',
        OAUTH_CREDENTIALS_DIR: process.env.OAUTH_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      error_file: './logs/oauth-error.log',
      out_file: './logs/oauth-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-calendar-test',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_calendar_test --transport sse --host 0.0.0.0 --port 11001',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        // OAuth test environment
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      error_file: './logs/google-calendar-test-error.log',
      out_file: './logs/google-calendar-test-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // ============================================================================
    // GOOGLE WORKSPACE TOOLS - Ports 11002-11010
    // Individual service tools for specific Google Workspace functionality
    // ============================================================================

    {
      name: 'google-calendar',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_calendar --transport sse --host 0.0.0.0 --port 11002',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-calendar-error.log',
      out_file: './logs/google-calendar-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-gmail',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_gmail --transport sse --host 0.0.0.0 --port 11003',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-gmail-error.log',
      out_file: './logs/google-gmail-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-drive',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_drive --transport sse --host 0.0.0.0 --port 11004',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-drive-error.log',
      out_file: './logs/google-drive-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-docs',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_docs --transport sse --host 0.0.0.0 --port 11005',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-docs-error.log',
      out_file: './logs/google-docs-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-sheets',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_sheets --transport sse --host 0.0.0.0 --port 11006',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-sheets-error.log',
      out_file: './logs/google-sheets-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-slides',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_slides --transport sse --host 0.0.0.0 --port 11007',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-slides-error.log',
      out_file: './logs/google-slides-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-forms',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_forms --transport sse --host 0.0.0.0 --port 11008',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-forms-error.log',
      out_file: './logs/google-forms-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-tasks',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_tasks --transport sse --host 0.0.0.0 --port 11009',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-tasks-error.log',
      out_file: './logs/google-tasks-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'google-chat',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_chat --transport sse --host 0.0.0.0 --port 11010',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/google-chat-error.log',
      out_file: './logs/google-chat-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // ============================================================================
    // GOOGLE WORKSPACE UNIFIED - Port 11011
    // Comprehensive all-in-one Google Workspace integration
    // ============================================================================

    {
      name: 'google-workspace',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.google_workspace --transport sse --host 0.0.0.0 --port 11011',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/google-workspace-error.log',
      out_file: './logs/google-workspace-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // ============================================================================
    // GENIE & MESSAGING - Ports 11012-11020
    // ============================================================================

    {
      name: 'genie-omni',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.genie_omni --transport sse --host 0.0.0.0 --port 11012',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GENIE_OMNI_API_KEY: process.env.GENIE_OMNI_API_KEY || '',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/genie-omni-error.log',
      out_file: './logs/genie-omni-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'evolution-api',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.evolution_api --transport sse --host 0.0.0.0 --port 11013',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        EVOLUTION_API_BASE_URL: process.env.EVOLUTION_API_BASE_URL || 'http://localhost:8080',
        EVOLUTION_API_API_KEY: process.env.EVOLUTION_API_API_KEY || '',
        EVOLUTION_API_INSTANCE: process.env.EVOLUTION_API_INSTANCE || 'default',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/evolution-api-error.log',
      out_file: './logs/evolution-api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'omni',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.omni --transport sse --host 0.0.0.0 --port 11014',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        OMNI_BASE_URL: process.env.OMNI_BASE_URL || 'http://localhost:8080',
        OMNI_API_KEY: process.env.OMNI_API_KEY || '',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/omni-error.log',
      out_file: './logs/omni-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // ============================================================================
    // UNIVERSAL TOOLS - Ports 11021-11030
    // ============================================================================

    {
      name: 'openapi',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.openapi --transport sse --host 0.0.0.0 --port 11021',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        OPENAPI_OPENAPI_URL: process.env.OPENAPI_OPENAPI_URL || '',
        OPENAPI_API_KEY: process.env.OPENAPI_API_KEY || '',
        OPENAPI_BASE_URL: process.env.OPENAPI_BASE_URL || '',
        OPENAPI_NAME: process.env.OPENAPI_NAME || 'OpenAPI',
        OPENAPI_INSTRUCTIONS: process.env.OPENAPI_INSTRUCTIONS || '',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/openapi-error.log',
      out_file: './logs/openapi-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'wait',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.wait --transport sse --host 0.0.0.0 --port 11022',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {},
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      error_file: './logs/wait-error.log',
      out_file: './logs/wait-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'json-to-google-docs',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.json_to_google_docs --transport sse --host 0.0.0.0 --port 11023',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GOOGLE_MCP_CREDENTIALS_DIR: process.env.GOOGLE_MCP_CREDENTIALS_DIR || '~/.credentials',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/json-to-google-docs-error.log',
      out_file: './logs/json-to-google-docs-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // ============================================================================
    // AGENT TOOLS - Ports 11031-11040
    // ============================================================================

    {
      name: 'genie-tool',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.genie_tool --transport sse --host 0.0.0.0 --port 11031',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {},
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/genie-tool-error.log',
      out_file: './logs/genie-tool-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    {
      name: 'gemini-assistant',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.gemini_assistant --transport sse --host 0.0.0.0 --port 11032',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        GEMINI_API_KEY: process.env.GEMINI_API_KEY || '',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/gemini-assistant-error.log',
      out_file: './logs/gemini-assistant-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // ============================================================================
    // EXPERIMENTAL - Ports 11041-11050
    // ============================================================================

    {
      name: 'spark',
      script: 'uv',
      args: 'run python -m automagik_tools.tools.spark --transport sse --host 0.0.0.0 --port 11041',
      cwd: '/home/namastex/workspace/automagik-tools',
      interpreter: 'none',
      env: {
        SPARK_API_URL: process.env.SPARK_API_URL || '',
        SPARK_API_KEY: process.env.SPARK_API_KEY || '',
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/spark-error.log',
      out_file: './logs/spark-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Note: hive tool directory does not exist - remove or create before enabling
    // {
    //   name: 'hive',
    //   script: 'uv',
    //   args: 'run python -m automagik_tools.tools.hive --transport sse --host 0.0.0.0 --port 11042',
    //   cwd: '/home/namastex/workspace/automagik-tools',
    //   interpreter: 'none',
    //   env: {
    //     HIVE_BASE_URL: process.env.HIVE_BASE_URL || 'http://localhost:3000',
    //     HIVE_API_KEY: process.env.HIVE_API_KEY || '',
    //   },
    //   instances: 1,
    //   autorestart: true,
    //   watch: false,
    //   max_memory_restart: '500M',
    //   error_file: './logs/hive-error.log',
    //   out_file: './logs/hive-out.log',
    //   log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    // },
  ],
};
