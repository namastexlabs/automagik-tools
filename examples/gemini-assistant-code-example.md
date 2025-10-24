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

**Command:**
```python
consult_gemini(
    problem_description="Need to optimize this React dashboard component for better performance",
    attached_files=[
        "/path/to/src/components/Dashboard.jsx",
        "/path/to/src/hooks/useData.js"
    ],
    file_descriptions={
        "/path/to/src/components/Dashboard.jsx": "Main dashboard with performance issues - re-renders too often",
        "/path/to/src/hooks/useData.js": "Custom hook for data fetching"
    },
    specific_question="How can I reduce unnecessary re-renders and improve data fetching?",
    preferred_approach="optimize"
)
```

**Expected Response:**
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

**Initial Query:**
```python
consult_gemini(
    problem_description="Getting 'Cannot read property of undefined' error in production",
    code_context="""
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
    """,
    specific_question="Why am I getting this error and how do I fix it?",
    preferred_approach="debug"
)
```

**Expected Response:**
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

**Follow-up Query:**
```python
consult_gemini(
    session_id="<session_id_from_previous>",
    specific_question="I implemented your fix but now getting CORS errors. How do I handle that?",
    additional_context="Added error handling, but API calls are being blocked by CORS policy",
    preferred_approach="follow-up"
)
```

**Expected Response:**
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

**Command:**
```python
list_sessions()
```

**Expected Response:**
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

```python
consult_gemini(
    problem_description="Designing a microservices architecture for e-commerce platform",
    attached_files=[
        "/docs/architecture-proposal.md",
        "/src/services/order-service/main.py",
        "/src/services/payment-service/main.py"
    ],
    specific_question="""
    Review this microservices design and provide feedback on:
    1. Service boundaries and responsibilities
    2. Communication patterns (sync vs async)
    3. Data consistency strategies
    4. Potential bottlenecks
    5. Scalability concerns
    """,
    preferred_approach="review"
)
```

### Scenario 2: Performance Optimization

```python
consult_gemini(
    problem_description="API endpoint taking 5+ seconds to respond under load",
    attached_files=[
        "/src/api/routes/products.js",
        "/src/database/queries.js",
        "/src/cache/redis.js"
    ],
    file_descriptions={
        "/src/api/routes/products.js": "Product listing endpoint with filters",
        "/src/database/queries.js": "Database query functions",
        "/src/cache/redis.js": "Redis caching layer"
    },
    specific_question="Identify performance bottlenecks and suggest optimizations",
    preferred_approach="optimize"
)
```

### Scenario 3: Security Audit

```python
consult_gemini(
    problem_description="Security review before production deployment",
    attached_files=[
        "/src/auth/middleware.js",
        "/src/api/routes/users.js",
        "/src/database/models/user.js"
    ],
    specific_question="""
    Perform security audit focusing on:
    1. Authentication vulnerabilities
    2. SQL injection risks
    3. XSS prevention
    4. Data validation
    5. Sensitive data exposure
    """,
    preferred_approach="review"
)
```

### Scenario 4: Refactoring Guidance

```python
# Initial consultation
session = consult_gemini(
    problem_description="Legacy codebase needs refactoring to modern patterns",
    code_context="[paste legacy code]",
    specific_question="What's the best approach to refactor this without breaking existing functionality?",
    preferred_approach="solution"
)

# Follow-up after implementation
consult_gemini(
    session_id=session["session_id"],
    specific_question="I've refactored the user service. Can you review the changes?",
    attached_files=["/src/services/user-service-new.js"],
    additional_context="Migrated from callbacks to async/await, added error handling",
    preferred_approach="review"
)
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

```python
consult_gemini(
    problem_description="Implementing real-time notifications",
    code_context="""
    Current implementation uses polling:
    setInterval(() => fetchNotifications(), 5000);
    
    Want to migrate to WebSockets for real-time updates.
    """,
    attached_files=[
        "/src/api/notifications.js",
        "/src/components/NotificationBell.jsx"
    ],
    specific_question="How do I migrate from polling to WebSockets without breaking existing functionality?",
    preferred_approach="solution"
)
```

### Multiple File Analysis

```python
consult_gemini(
    problem_description="Analyzing full authentication flow",
    attached_files=[
        "/src/auth/login.js",
        "/src/auth/register.js",
        "/src/auth/middleware.js",
        "/src/auth/jwt.js",
        "/src/database/models/user.js"
    ],
    file_descriptions={
        "/src/auth/login.js": "Login endpoint handler",
        "/src/auth/register.js": "User registration logic",
        "/src/auth/middleware.js": "Auth middleware for protected routes",
        "/src/auth/jwt.js": "JWT token generation and validation",
        "/src/database/models/user.js": "User model with password hashing"
    },
    specific_question="Review the entire authentication flow for security issues and best practices",
    preferred_approach="review"
)
```

## Troubleshooting

### Common Issues

1. **"Service account credentials not found"**
   - Ensure `GEMINI_API_KEY` is set correctly
   - Verify API key is valid at [Google AI Studio](https://aistudio.google.com/app/apikey)

2. **"Session not found"**
   - Session may have expired (default: 1 hour)
   - Use `list_sessions()` to see active sessions
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
