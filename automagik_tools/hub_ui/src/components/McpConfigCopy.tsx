import { useState } from 'react';
import { Wrench, Check } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

export function McpConfigCopy() {
  const [copied, setCopied] = useState(false);

  const getMcpConfig = () => {
    // TODO: Implement /api/tokens/generate endpoint for MCP authentication
    // MCP servers run outside browser context and cannot use HTTP-only cookies
    const accessToken = 'your-access-token-here';

    // Construct the Hub URL - default to localhost:8884 for development
    // In production, this would typically be the same origin
    const hubUrl = import.meta.env.VITE_HUB_URL || 'http://localhost:8884';

    return {
      mcpServers: {
        'automagik-tools-hub': {
          command: 'uvx',
          args: ['--from', 'automagik-tools', 'automagik-tools', 'serve-all', '--transport', 'stdio'],
          env: {
            HUB_MODE: 'http',
            HUB_URL: hubUrl,
            HUB_ACCESS_TOKEN: accessToken,  // Placeholder - see TODO above
          },
        },
      },
    };
  };

  const handleCopy = async () => {
    try {
      const config = getMcpConfig();
      const configJson = JSON.stringify(config, null, 2);

      await navigator.clipboard.writeText(configJson);

      setCopied(true);
      toast.success('MCP config copied to clipboard!', {
        description: 'Paste this into your Claude Code or Cursor settings',
      });

      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy config', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={handleCopy}
      className="h-9 w-9"
      aria-label="Copy MCP Config"
      title="Copy MCP configuration for Claude Code / Cursor"
    >
      {copied ? (
        <Check className="h-4 w-4 text-success" />
      ) : (
        <Wrench className="h-4 w-4" />
      )}
    </Button>
  );
}
