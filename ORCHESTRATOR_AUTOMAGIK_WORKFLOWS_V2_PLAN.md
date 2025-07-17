# 🎯 ORCHESTRATOR PLAN: Smart Automagik-Workflows V2 Refactor

## 📋 Executive Summary

Comprehensive refactor plan for automagik-workflows tool into an intelligent streaming workflow orchestration system with real-time feedback, session management, and agent coordination capabilities.

## 🔍 Current Investigation Results

### Automagik-Workflows API Analysis ✅

**Base URL**: `http://localhost:28881/api/v1/workflows/claude-code`

**Critical Requirements**:
- **Stream Input**: `input_format: "stream-json"` is MANDATORY
- **Authentication**: `x-api-key` header required

**Key Endpoints**:
```
POST /run/{workflow_name}                    # Execute workflow
POST /run/{run_id}/add-message              # Real-time feedback injection
GET  /run/{run_id}/status                   # Status polling
GET  /runs                                  # List all runs
POST /run/{run_id}/cleanup                  # Cleanup
POST /run/{run_id}/kill                     # Force stop
GET  /run/{run_id}/message-queue            # Message queue status
```

**Workflow Request Schema**:
```json
{
  "message": "string (required)",
  "input_format": "stream-json (required)",
  "session_id": "string (optional)",
  "session_name": "string (optional)", 
  "max_turns": "integer (1-200)",
  "repository_url": "string (optional)",
  "git_branch": "string (optional)",
  "timeout": "integer (60-14400)",
  "user_id": "string (optional)"
}
```

**Available Workflows**:
- `architect` - Design system architecture
- `implement` - Feature implementation
- `test` - Comprehensive testing
- `review` - Code review and quality
- `fix` - Surgical fixes
- `refactor` - Code improvement
- `document` - Documentation generation

### FastMCP Streaming Capabilities ✅

**Real-time Features**:
- **Progress Streaming**: `Context.report_progress()` for live updates
- **Push Notifications**: Server-to-client without polling
- **StreamableHttpTransport**: Bidirectional HTTP streaming (recommended)
- **WebSocket Support**: `WSTransport` available
- **List Change Notifications**: Automatic updates for tool/resource changes

**Transport Options**:
- `StreamableHttpTransport` (recommended for production)
- `SSETransport` (Server-Sent Events, legacy)
- `WSTransport` (WebSocket support)
- `FastMCPTransport` (in-memory, testing)

## 🧠 Smart Tool Design Architecture

### Core Interface Functions

```python
# 1. Smart Workflow Orchestration
@mcp.tool()
async def run_workflow(
    workflow_name: str,           # architect, builder, tester, etc.
    message: str,                # Natural language task description
    session_name: Optional[str] = None,  # Human-readable identifier
    continue_session: Optional[str] = None, # Resume by session name
    max_turns: int = 50,
    repository_url: Optional[str] = None,
    git_branch: Optional[str] = None,
    ctx: Context
) -> dict

# 2. Real-time Feedback Injection  
@mcp.tool()
async def send_feedback(
    session_id: str,
    feedback: str,               # Real-time guidance/corrections
    message_type: Literal["user", "system"] = "user",
    ctx: Context
) -> dict

# 3. Intelligent Session Management
@mcp.tool()
async def list_sessions(
    active_only: bool = True,
    ctx: Context  
) -> dict

@mcp.tool()
async def get_session_status(
    session_id: str,
    detailed: bool = True,
    ctx: Context
) -> dict

# 4. Workflow Discovery
@mcp.tool()
async def list_workflows(ctx: Context) -> dict
```

### Smart Features Architecture

#### 🔄 Real-time Progress Streaming
```python
class ProgressTracker:
    async def run_workflow_with_progress(self, ctx: Context, ...):
        # Start workflow with stream-json input format
        run_result = await self.client.run_workflow(
            workflow_name=workflow_name,
            payload={
                "message": message,
                "input_format": "stream-json",  # REQUIRED!
                "session_id": session_id,
                "session_name": session_name,
                "max_turns": max_turns,
                "repository_url": repository_url,
                "git_branch": git_branch
            }
        )
        
        # Real-time progress reporting using FastMCP
        run_id = run_result["run_id"]
        while not self._is_complete(run_id):
            status = await self.client.get_status(run_id)
            
            # Stream progress to client via FastMCP Context
            await ctx.report_progress(
                progress=status.get("current_turn", 0),
                total=status.get("max_turns", max_turns),
                message=f"Turn {status.get('current_turn', 0)}/{max_turns}: {status.get('current_action', 'Processing...')}"
            )
            
            await asyncio.sleep(8)  # Intelligent polling interval
        
        return await self.client.get_status(run_id, detailed=True)
```

#### 🧠 Intelligent Session Management  
```python
class SessionManager:
    def __init__(self, client: AutomagikWorkflowsClient):
        self.client = client
        self._session_cache = {}
    
    async def find_session_by_name(self, session_name: str) -> Optional[str]:
        """Find session ID by human-readable name"""
        runs = await self.client.list_runs()
        for run in runs.get("runs", []):
            if run.get("session_name") == session_name:
                return run.get("session_id")
        return None
    
    async def smart_continue_session(self, session_name: str, ctx: Context) -> Optional[str]:
        """Resume session by name or create new if not found"""
        session_id = await self.find_session_by_name(session_name)
        if session_id:
            await ctx.report_progress(0, 1, f"Resuming session: {session_name}")
            return session_id
        else:
            await ctx.report_progress(0, 1, f"Creating new session: {session_name}")
            return None
```

#### 💬 Real-time Feedback Loop
```python
class FeedbackLoop:
    async def inject_feedback(self, session_id: str, feedback: str, ctx: Context):
        """Send real-time feedback to running workflow"""
        result = await self.client.add_message(
            run_id=session_id,
            message=feedback,
            message_type="user"
        )
        
        # Notify client of successful injection
        await ctx.report_progress(
            progress=1,
            total=1, 
            message=f"Feedback injected: {feedback[:50]}..."
        )
        
        return result
```

## 🏗️ Implementation Strategy

### Phase 1: Core Infrastructure (2-3 hours)
```
automagik_tools/tools/automagik_workflows_v2/
├── __init__.py              # FastMCP exports
├── __main__.py              # CLI compatibility  
├── server.py                # Main FastMCP server
├── config.py                # Configuration management
├── client.py                # HTTP client for API calls
├── session_manager.py       # Smart session handling
├── progress_tracker.py      # Real-time progress system
├── models.py                # Pydantic models
└── README.md               # Documentation
```

**Configuration Schema**:
```python
class AutomagikWorkflowsV2Config(BaseSettings):
    api_base_url: str = "http://localhost:28881"
    api_key: str = Field(alias="AUTOMAGIK_WORKFLOWS_V2_API_KEY")
    timeout: int = 7200
    polling_interval: int = 8
    max_retries: int = 3
    input_format: str = "stream-json"  # Required parameter
```

### Phase 2: Smart Functions (3-4 hours)
- **Real-time Progress**: `Context.report_progress()` integration
- **Session Continuity**: Smart session discovery and resumption
- **Feedback Injection**: Real-time message injection to running workflows
- **Intelligent Polling**: Adaptive polling with backoff strategies

### Phase 3: Comprehensive Testing (4-5 hours)
- **Unit Tests**: Component testing with mocks
- **MCP Protocol Tests**: FastMCP compliance validation
- **Integration Tests**: End-to-end with real API
- **Streaming Tests**: Real-time features validation
- **Performance Tests**: Latency and concurrent workflow testing

## 🎯 Natural Language Interface Design

### Orchestrator-Friendly Commands
```python
# Start new orchestrated workflow
await run_workflow(
    workflow_name="architect",
    message="Design microservices architecture for automagik-tools",
    session_name="automagik-architecture-design",
    repository_url="https://github.com/namastex888/automagik-tools",
    ctx=ctx
)

# Send real-time guidance to running workflow  
await send_feedback(
    session_id="arch-session-123",
    feedback="Focus on MCP tool patterns and FastMCP integration",
    ctx=ctx
)

# Resume previous orchestration session
await run_workflow(
    workflow_name="builder", 
    message="Continue implementation based on architecture design",
    continue_session="automagik-architecture-design",
    ctx=ctx
)
```

### Agent Hive Coordination Examples
```python
# The orchestrator can seamlessly coordinate multiple agents:

# 1. ANALYZER: Start analysis with specific focus
await run_workflow(
    "architect", 
    "Analyze automagik-tools for MCP tool patterns", 
    session_name="pattern-analysis"
)

# 2. Real-time guidance during analysis
await send_feedback(
    "pattern-session-123",
    "Focus on FastMCP Context.report_progress patterns"
)

# 3. BUILDER: Seamless handoff to implementation
await run_workflow(
    "implement",
    "Implement streaming workflow tool based on analysis", 
    continue_session="pattern-analysis"
)

# 4. TESTER: Continue with testing phase
await run_workflow(
    "test",
    "Create comprehensive test suite for streaming features",
    continue_session="pattern-analysis"
)
```

## 📊 Linear Epic & Tasks Created

### Epic
**[NMSTX-366](https://linear.app/namastex/issue/NMSTX-366/tool-automagik-workflows-v2-smart-streaming-workflow-orchestration)**: Smart Streaming Workflow Orchestration

### Implementation Tasks
1. **[NMSTX-367](https://linear.app/namastex/issue/NMSTX-367/builder-core-infrastructure-automagik-workflows-v2-project-setup)**: Core Infrastructure Setup (2-3 hours)
   - Project structure and FastMCP integration
   - Configuration management
   - HTTP client foundation
   - Registration and integration

2. **[NMSTX-368](https://linear.app/namastex/issue/NMSTX-368/builder-smart-functions-real-time-streaming-and-session-management)**: Smart Functions Implementation (3-4 hours)
   - Core MCP tool functions
   - Real-time progress streaming
   - Session management intelligence
   - Feedback injection system

3. **[NMSTX-369](https://linear.app/namastex/issue/NMSTX-369/tester-comprehensive-testing-and-integration-validation)**: Comprehensive Testing (4-5 hours)
   - Unit tests with >30% coverage
   - MCP protocol compliance
   - Integration and streaming tests
   - Performance validation

**Total Estimated Time**: 9-12 hours

## 🚀 Success Metrics & Goals

### Technical Success Criteria
- **Real-time Progress**: Live updates via `Context.report_progress()`
- **Session Continuity**: Resume workflows seamlessly by name
- **Agent Coordination**: Enable orchestrator to manage agent hives  
- **Zero Polling**: Push notifications eliminate client polling
- **Natural Language**: Intuitive interface for orchestrators

### Performance Targets
- **Workflow Startup**: < 5 seconds
- **Progress Update Latency**: < 1 second
- **Session Discovery**: < 2 seconds
- **Feedback Injection**: < 500ms
- **Concurrent Workflows**: Support 10+ simultaneous

### Quality Standards
- **Test Coverage**: >30% overall, >80% core functions
- **Error Handling**: All error paths covered
- **MCP Compliance**: Full FastMCP protocol adherence
- **Documentation**: Complete API documentation

## 🔄 Agent Hive Orchestration Vision

This tool will enable unprecedented orchestrator capabilities:

### Multi-Agent Workflows
```python
# Orchestrator coordinates specialized agents across phases:
# 1. Analysis Phase: ANALYZER agent studies requirements
# 2. Design Phase: ARCHITECT agent creates technical design  
# 3. Implementation Phase: BUILDER agent codes the solution
# 4. Testing Phase: TESTER agent validates functionality
# 5. Review Phase: VALIDATOR agent ensures quality
# 6. Deployment Phase: DEPLOYER agent handles release
```

### Seamless Handoffs
- **Session Continuity**: Work flows seamlessly between agents
- **Context Preservation**: Full conversation history maintained
- **Smart Resumption**: Pick up any workflow from any point
- **Real-time Coordination**: Live guidance during execution

### Intelligence Features
- **Pattern Recognition**: Learn from successful workflows
- **Adaptive Polling**: Optimize based on workflow complexity
- **Error Recovery**: Intelligent retry and fallback strategies
- **Resource Management**: Efficient handling of concurrent workflows

## 🔄 Technical Flow Example (Step by Step)

### Real-World Scenario: Building JWT Authentication System

**Step 1: User Intent**
User: "Build a JWT authentication system for my Node.js app"

**Step 2: Orchestrator Agent Uses automagik-workflows-v2 Tool**
Orchestrator calls our MCP tool with workflow_name="architect", message="Design JWT authentication system for Node.js", session_name="auth-system-project"

**Step 3: Our MCP Tool Calls the Automagik API**
Tool makes HTTP POST to /api/v1/workflows/claude-code/run/architect with input_format="stream-json" (required), gets back run_id="workflow-abc-123" and session_id="session-xyz-789"

**Step 4: Real-time Progress Streaming**
Tool starts intelligent polling every 8 seconds, calls GET /status endpoint, streams progress to user via FastMCP Context.report_progress() showing "Turn 3/10: Designing database schema..."

**Step 5: User Sees Real-time Updates**
User interface shows live progress: "Turn 4/10: Creating API endpoints...", "Turn 5/10: Adding JWT middleware..."

**Step 6: Orchestrator Sends Real-time Feedback**
Orchestrator calls send_feedback() with guidance: "Make sure to include refresh token rotation"

**Step 7: Our Tool Injects Message**
Tool calls POST /add-message API to inject real-time feedback into running workflow

**Step 8: Workflow Completes, Handoff to Next Agent**
Architecture phase done, orchestrator calls run_workflow() with workflow_name="implement", continue_session="auth-system-project" for seamless handoff

**Step 9: Session Continuity Magic**
Tool finds existing session by name via GET /runs, continues with same session_id for context preservation across different workflow phases

## 🚀 Revolutionary FastMCP Enhancements

### 1. Elicitation-Powered Dynamic Interaction
- **Dynamic Parameter Collection**: Tools can request missing information during execution instead of upfront
- **Structured Data Validation**: Automatic JSON schema to Python dataclass conversion with type safety
- **Interactive Workflow Adaptation**: Workflows can ask for clarification or additional requirements mid-execution
- **User Choice Integration**: Handle accept/decline/cancel responses for flexible workflow control

### 2. Ultra-Smart Tool Design (Minimal Interface)
- **Dynamic Workflow Discovery**: Fetch available workflows at runtime and populate as enum options
- **Self-Describing Tools**: Tools that adapt their parameters based on discovered capabilities
- **Intelligent Parameter Inference**: Use elicitation to gather only necessary parameters
- **Context-Aware Behavior**: Tools that modify behavior based on available data and session state

### 3. Advanced Message Handling
- **Stateful Message Handlers**: Replace dumb polling with intelligent reactive handling
- **Workflow State Management**: Custom handlers that track and modify workflow context
- **Event-Driven Coordination**: Message routing for sophisticated multi-workflow coordination
- **Dynamic Resource Adaptation**: React to resource availability changes in real-time

## 🎯 Optimized Tool Architecture

### Single Super-Tool Approach
Instead of 5 separate tools, create ONE intelligent orchestration tool that:
- **Discovers Workflows Dynamically**: Fetches available workflows and presents as enum choices
- **Uses Elicitation for Smart Interaction**: Requests additional parameters only when needed
- **Handles All Workflow Operations**: Run, feedback, status, session management in one interface
- **Adapts to Available Capabilities**: Modifies behavior based on discovered API features

### Enhanced Session Management
- **MessageHandler Integration**: Reactive session state tracking instead of polling
- **Dynamic Session Discovery**: Real-time session list updates via notifications
- **Intelligent Session Routing**: Automatic session handoffs between workflow phases
- **Context Preservation**: Full conversation history and state maintained across handoffs

## 🔮 Future Enhancements

### Advanced Features (Post-MVP)
- **Workflow Templating**: Reusable orchestration patterns with elicitation-based customization
- **Dependency Management**: Automatic workflow sequencing with dynamic parameter passing
- **Resource Optimization**: Smart resource allocation based on real-time availability
- **Analytics Dashboard**: Workflow performance metrics with interactive drill-down
- **AI-Powered Routing**: Intelligent agent selection based on workflow requirements

### Integration Opportunities  
- **Linear Integration**: Automatic issue creation with elicitation-based project selection
- **Git Integration**: Dynamic repository discovery with elicitation-based branch selection
- **Slack/Discord**: Real-time notifications with interactive response handling
- **Monitoring**: Performance dashboards with elicitation-based metric customization

## 📝 Next Steps

1. **Implement Single Super-Tool**: Create one intelligent orchestration tool with dynamic capabilities
2. **Integrate Elicitation**: Add dynamic parameter collection for enhanced user interaction
3. **Implement Message Handlers**: Replace polling with reactive message-driven architecture
4. **Begin Implementation**: Start with NMSTX-367 (Core Infrastructure) with enhanced specifications
5. **Orchestrator Integration**: Test with real orchestration scenarios using new capabilities

## 🏆 Vision Achievement

This refactor will create **the most intelligent natural language workflow tool ever built** that transforms workflow orchestration from a static, polling-based system into a dynamic, elicitation-powered, message-driven platform that:

- **Adapts in Real-Time**: Discovers capabilities and adjusts behavior dynamically
- **Interacts Intelligently**: Uses elicitation for smart parameter collection and user guidance
- **Coordinates Seamlessly**: Enables unprecedented orchestrator capabilities with agent hive management
- **Responds Reactively**: Message-driven architecture eliminates polling delays
- **Learns Continuously**: Self-improving through dynamic capability discovery and user interaction patterns

The result will be a tool that not only executes workflows but becomes an intelligent orchestration partner, enabling complex multi-phase development with natural language control, real-time adaptation, and seamless agent collaboration.