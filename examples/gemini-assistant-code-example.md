# Gemini Assistant Code Review Example

This example demonstrates how to use the Gemini Assistant tool to get expert code reviews, architectural insights, and solutions for complex programming problems with full file context.

## Use Case Description

Use Gemini Assistant when you need:
- Deep code reviews with architectural insights
- Solutions to complex programming problems
- Analysis of large codebases with multiple files
- Performance optimization recommendations
- Debugging assistance with full context
- Alternative implementation approaches with trade-offs
- Follow-up discussions about code changes

Perfect for developers who want a second opinion on complex code, need help debugging tricky issues, or want to explore different architectural approaches.

## Setup

### Prerequisites

1. **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Code Files**: Files you want to analyze or get help with
3. **Python 3.12+**: For running automagik-tools

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - Gemini Configuration
GEMINI_MODEL=gemini-2.0-flash-exp        # Default model
GEMINI_SESSION_TIMEOUT=3600              # Session timeout (1 hour)
GEMINI_MAX_TOKENS=8192                   # Max tokens per response
GEMINI_TEMPERATURE=0.2                   # Response temperature
GEMINI_MAX_SESSIONS=10                   # Max concurrent sessions
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool gemini-assistant --transport stdio

# Run with SSE transport
uvx automagik-tools tool gemini-assistant --transport sse --port 8000

# Run with HTTP transport
uvx automagik-tools tool gemini-assistant --transport http --port 8001
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-assistant": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "gemini-assistant",
        "--transport",
        "stdio"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.0-flash-exp",
        "GEMINI_SESSION_TIMEOUT": "3600"
      }
    }
  }
}
```

### For Cursor

Add this to your Cursor MCP configuration (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "gemini-assistant": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "gemini-assistant",
        "--transport",
        "stdio"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

### Minimal Configuration

```json
{
  "mcpServers": {
    "gemini-assistant": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "gemini-assistant"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

## Expected Output

### 1. Code Review with File Attachments

**In Claude Desktop, say:**
```
I need help optimizing this React dashboard component for better performance. I've attached the Dashboard.jsx file (main dashboard with performance issues - re-renders too often) and useData.js (custom hook for data fetching). How can I reduce unnecessary re-renders and improve data fetching?
```

**Claude responds:**
```markdown
I've analyzed your Dashboard component and useData hook. Here are the key performance issues and solutions:

## Performance Issues Identified

1. **Unnecessary Re-renders**
   - Dashboard re-renders on every parent update
   - Missing React.memo() optimization
   - Inline function definitions causing child re-renders

2. **Data Fetching Problems**
   - No request deduplication
   - Missing cache invalidation strategy
   - Fetching on every render instead of mount

3. **State Management**
   - Too many useState calls causing multiple renders
   - State updates not batched

## Recommended Solutions

### 1. Memoize the Dashboard Component
```javascript
import React, { memo, useMemo, useCallback } from 'react';

const Dashboard = memo(({ userId, filters }) => {
  // Component logic
}, (prevProps, nextProps) => {
  // Custom comparison for optimization
  return prevProps.userId === nextProps.userId &&
         JSON.stringify(prevProps.filters) === JSON.stringify(nextProps.filters);
});
```

### 2. Optimize useData Hook
```javascript
export const useData = (userId) => {
  const queryClient = useQueryClient();
  
  return useQuery({
    queryKey: ['userData', userId],
    queryFn: () => fetchUserData(userId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false,
  });
};
```

### 3. Use useCallback for Event Handlers
```javascript
const handleFilterChange = useCallback((newFilters) => {
  setFilters(newFilters);
}, []);
```

## Expected Performance Improvements
- **Re-renders**: Reduced by ~70%
- **API Calls**: Reduced by ~85% with caching
- **Initial Load**: ~40% faster
- **User Interactions**: ~60% more responsive

## Implementation Order
1. Add React.memo() to Dashboard (quick win)
2. Implement useCallback for handlers
3. Migrate to React Query for data fetching
4. Add proper cache invalidation

Would you like me to provide the complete refactored code or explain any of these optimizations in more detail?
```

### 2. Debugging Session with Follow-ups

**In Claude Desktop, say for the initial query:**
```
I'm getting a 'Cannot read property of undefined' error in production. Here's my code:

// User service
async function getUserProfile(userId) {
  const response = await fetch(`/api/users/${userId}`);
  const data = await response.json();
  return data.user.profile;
}

// Component
const UserProfile = ({ userId }) => {
  const [profile, setProfile] = useState(null);
  
  useEffect(() => {
    getUserProfile(userId).then(setProfile);
  }, [userId]);
  
  return <div>{profile.name}</div>;
};

Why am I getting this error and how do I fix it?
```

**Claude responds:**
```markdown
I found the issue! There are actually **three** potential sources of the undefined error:

## Root Causes

1. **API Response Structure**
   - `data.user.profile` assumes nested structure
   - If API returns `data.profile` directly, `data.user` is undefined

2. **Race Condition**
   - Component renders before profile is loaded
   - Accessing `profile.name` when profile is still null

3. **Missing Error Handling**
   - No handling for failed API calls
   - No validation of response structure

## Immediate Fix

```javascript
const UserProfile = ({ userId }) => {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    getUserProfile(userId)
      .then(setProfile)
      .catch(setError);
  }, [userId]);
  
  if (error) return <div>Error loading profile</div>;
  if (!profile) return <div>Loading...</div>;
  
  return <div>{profile.name}</div>;
};
```

## Better Solution with Validation

```javascript
async function getUserProfile(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Validate response structure
    if (!data?.user?.profile && !data?.profile) {
      throw new Error('Invalid response structure');
    }
    
    // Handle both response formats
    return data.user?.profile || data.profile;
  } catch (error) {
    console.error('Failed to fetch user profile:', error);
    throw error;
  }
}
```

The error is happening because you're not checking if `profile` exists before accessing `profile.name`. Add the loading/error states as shown above.
```

**For the follow-up query, in Claude Desktop say:**
```
I implemented your fix but now I'm getting CORS errors. How do I handle that? I've added error handling, but API calls are being blocked by CORS policy.
```

**Claude responds:**
```markdown
Good catch! CORS errors are a different issue. Since you've fixed the undefined error, let's tackle CORS:

## CORS Solutions

### Option 1: Backend Configuration (Recommended)
```javascript
// Express.js example
const cors = require('cors');

app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
```

### Option 2: Proxy in Development
```javascript
// package.json
{
  "proxy": "http://localhost:8080"
}

// Then use relative URLs
const response = await fetch(`/api/users/${userId}`);
```

### Option 3: Include Credentials
```javascript
const response = await fetch(`/api/users/${userId}`, {
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  }
});
```

## Quick Test
Try this to verify CORS is the only issue:
```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://your-api.com/api/users/123 -v
```

Which backend framework are you using? I can provide more specific configuration.
```

### 3. List Active Sessions

**In Claude Desktop, say:**
```
Show me my active Gemini Assistant sessions
```

**Claude responds:**
```json
{
  "sessions": [
    {
      "session_id": "abc123def456",
      "created_at": "2024-01-15T10:30:00Z",
      "last_activity": "2024-01-15T10:45:00Z",
      "problem_description": "React dashboard performance optimization",
      "message_count": 5,
      "attached_files": 2,
      "expires_at": "2024-01-15T11:30:00Z"
    },
    {
      "session_id": "xyz789ghi012",
      "created_at": "2024-01-15T09:15:00Z",
      "last_activity": "2024-01-15T09:20:00Z",
      "problem_description": "Debugging undefined property error",
      "message_count": 2,
      "attached_files": 0,
      "expires_at": "2024-01-15T10:15:00Z"
    }
  ],
  "total_sessions": 2,
  "max_sessions": 10
}
```

## Real-World Usage Scenarios

### Scenario 1: Architecture Review

**In Claude Desktop, say:**
```
I'm designing a microservices architecture for an e-commerce platform. I've attached the architecture proposal document and the main files for the order and payment services. Please review this microservices design and provide feedback on:
1. Service boundaries and responsibilities
2. Communication patterns (sync vs async)
3. Data consistency strategies
4. Potential bottlenecks
5. Scalability concerns
```

### Scenario 2: Performance Optimization

**In Claude Desktop, say:**
```
I have an API endpoint that's taking 5+ seconds to respond under load. I've attached the product listing endpoint with filters, the database query functions, and the Redis caching layer files. Please identify performance bottlenecks and suggest optimizations.
```

### Scenario 3: Security Audit

**In Claude Desktop, say:**
```
I need a security review before production deployment. I've attached the authentication middleware, user routes, and user model files. Please perform a security audit focusing on:
1. Authentication vulnerabilities
2. SQL injection risks
3. XSS prevention
4. Data validation
5. Sensitive data exposure
```

### Scenario 4: Refactoring Guidance

**In Claude Desktop, say for initial consultation:**
```
I have a legacy codebase that needs refactoring to modern patterns. Here's the legacy code: [paste legacy code]. What's the best approach to refactor this without breaking existing functionality?
```

**For follow-up after implementation, say:**
```
I've refactored the user service. I've attached the new file. Can you review the changes? I've migrated from callbacks to async/await and added error handling.
```

## Features Demonstrated

1. **File Attachments**: Upload actual code files for comprehensive analysis
2. **Session Management**: Continue conversations across multiple queries
3. **Context Caching**: Code context is cached per session for efficiency
4. **Multiple Approaches**: Solution, review, debug, optimize, explain, follow-up
5. **File Descriptions**: Provide context for each attached file
6. **Follow-up Questions**: Ask additional questions without resending code
7. **Session Tracking**: List and manage active consultation sessions

## Best Practices

1. **Provide Complete Context**: Include all relevant files and descriptions
2. **Be Specific**: Ask focused questions for better responses
3. **Use Sessions**: Continue conversations for related questions
4. **File Organization**: Attach files logically grouped by concern
5. **Clear Descriptions**: Explain what each file does and why it's relevant
6. **End Sessions**: Clean up when done to free resources
7. **Iterative Refinement**: Use follow-ups to dive deeper into solutions

## Advanced Usage

### Hybrid Context (Text + Files)

**In Claude Desktop, say:**
```
I'm implementing real-time notifications. My current implementation uses polling:
setInterval(() => fetchNotifications(), 5000);

I want to migrate to WebSockets for real-time updates. I've attached the notifications API file and the NotificationBell component. How do I migrate from polling to WebSockets without breaking existing functionality?
```

### Multiple File Analysis

**In Claude Desktop, say:**
```
I need to analyze the full authentication flow for security issues and best practices. I've attached the login endpoint handler, user registration logic, auth middleware for protected routes, JWT token generation and validation, and user model with password hashing files.
```

## Troubleshooting

### Common Issues

1. **"Service account credentials not found"**
   - Ensure `GEMINI_API_KEY` is set correctly
   - Verify API key is valid at [Google AI Studio](https://aistudio.google.com/app/apikey)

2. **"Session not found"**
   - Session may have expired (default: 1 hour)
   - Ask Claude to list active sessions
   - Start a new session if needed

3. **"File upload failed"**
   - Check file path is correct and accessible
   - Verify file size is within limits
   - Ensure file format is supported (text-based files)

4. **"RESOURCE_EXHAUSTED" error**
   - API quota exceeded
   - Wait and retry, or upgrade API plan
   - Reduce number of attached files

5. **Empty or incomplete responses**
   - Question may be too broad - be more specific
   - Context may be too large - focus on relevant code
   - Check API status and quotas

## Performance Tips

1. **Session Reuse**: Use sessions for related questions to avoid re-uploading files
2. **File Selection**: Only attach files directly relevant to the question
3. **Context Size**: Keep code context focused and concise
4. **Batch Questions**: Ask multiple related questions in one query
5. **Model Selection**: Use faster models for simple questions

## Security Considerations

- **API Key Protection**: Never expose API keys in code or logs
- **Code Privacy**: Be aware that code is sent to Google's API
- **Sensitive Data**: Remove secrets, keys, and PII before uploading
- **File Cleanup**: Sessions and files are automatically cleaned up
- **Rate Limiting**: Respect API rate limits to avoid blocking

## Next Steps

1. **Integrate with CI/CD**: Automate code reviews in your pipeline
2. **Create Templates**: Build reusable question templates
3. **Team Workflows**: Share sessions for collaborative reviews
4. **Custom Prompts**: Tailor preferred_approach for your needs
5. **Analytics**: Track common issues and improvements

## Additional Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://aistudio.google.com/)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
- [MCP Gemini Assistant](https://github.com/peterkrueck/mcp-gemini-assistant)
