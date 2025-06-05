# AutoMagik Tools: Technical Product Requirements Document (PRD)

## 📋 Executive Summary

**Product Vision**: Create two distinct user experiences for AutoMagik Tools - a zero-friction uvx-based experience for end users wanting instant MCP integrations, and a comprehensive make-based development environment for tool creators and deployers.

**Target Release**: Q4 2024
**Engineering Teams**: Planning, Architecture, Implementation, Code Review, Testing, Documentation

---

## 🎯 Product Strategy & User Segmentation

### Primary User Personas

#### 1. **End Users** (Zero-Installation Experience)
- **Profile**: AI practitioners, non-developers, business users
- **Goal**: Copy-paste MCP tool integration with AI assistants
- **Tools**: Claude Desktop, Cursor, Continue, other MCP clients
- **Approach**: `uvx automagik-tools` - no installation, no setup, just works

#### 2. **Developer Users** (Full Development Environment)
- **Profile**: Tool creators, platform developers, deployment engineers
- **Goal**: Create, test, and deploy custom MCP tools and servers
- **Tools**: Local development, CI/CD, cloud deployment
- **Approach**: `make` commands - full repository-based workflow

---

## 🏗️ Technical Architecture

### Core Design Principles

1. **Zero-Friction End User Experience**: uvx handles all dependencies and isolation
2. **Developer-First Tool Creation**: make commands for all development workflows
3. **Universal MCP Compatibility**: stdio, SSE, HTTP transports
4. **Production-Ready Deployment**: Cloud-native deployment options

### Transport Layer Strategy

```
End Users (uvx):
├── stdio transport → MCP clients (Claude, Cursor)
├── SSE transport → Web applications  
└── HTTP transport → API integrations

Developers (make):
├── Local development servers
├── Hot-reload development
├── Multi-tool orchestration
└── Cloud deployment pipelines
```

---

## 📊 Current State Analysis

### ✅ **Existing Capabilities**
- Comprehensive Makefile with help system
- OpenAPI → MCP tool generation (`make tool URL=url`)
- Multi-tool server (`make serve-all`)
- Development environment setup (`make install`)
- Testing framework (`make test`, `make test-coverage`)
- Publishing pipeline (`make publish`)
- FastMCP integration (`make fastmcp-*`)

### ❌ **Critical Gaps**
- No generic single-tool serving
- Documentation shows complex CLI instead of simple commands
- Missing developer workflow commands
- No deployment automation for SSE servers

---

## 🎯 Epic 1: End User Experience (uvx-Based)

**Objective**: Enable any user to integrate MCP tools in under 2 minutes with zero installation

### Story 1.1: Simplified Documentation & Examples
**Priority**: Critical | **Effort**: 4 hours

**Requirements**:
- Replace all CLI examples with uvx commands
- Create ready-to-paste JSON configurations for major MCP clients
- Add environment variable templates with clear instructions

**Technical Specifications**:
```bash
# Before (complex)
pip install automagik-tools
automagik-tools serve --tool evolution-api --transport stdio

# After (simple)
uvx automagik-tools serve --tool evolution-api --transport stdio
```

**Acceptance Criteria**:
- [ ] All README examples use uvx
- [ ] JSON configs provided for Claude Desktop, Cursor, Continue
- [ ] Environment variable documentation complete
- [ ] Zero installation steps required

### Story 1.2: Universal Tool Serving
**Priority**: Critical | **Effort**: 6 hours

**Technical Requirements**:
- Generic `uvx automagik-tools serve --tool TOOLNAME` command
- Support all transport methods (stdio, sse, http)
- Auto-detect tool configuration requirements
- Clear error messages for missing environment variables

**Implementation Details**:
```python
# CLI interface enhancement needed
@click.command()
@click.option('--tool', required=True, help='Tool name to serve')
@click.option('--transport', default='stdio', type=click.Choice(['stdio', 'sse', 'http']))
@click.option('--host', default='127.0.0.1')
@click.option('--port', default=8000, type=int)
def serve(tool, transport, host, port):
    """Serve a single MCP tool with specified transport"""
    # Implementation needed
```

**Acceptance Criteria**:
- [ ] Any discovered tool can be served individually
- [ ] All transport methods supported
- [ ] Environment validation with helpful error messages
- [ ] Works identically via uvx and local installation

---

## 🎯 Epic 2: Developer Experience (Make-Based)

**Objective**: Provide comprehensive development workflow for MCP tool creation and deployment

### Story 2.1: Missing Make Commands
**Priority**: High | **Effort**: 8 hours

**Required Commands**:

#### `make serve TOOL=toolname`
```makefile
serve: ## 🚀 Serve single tool (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make serve TOOL=<tool-name>); \
		exit 1; \
	fi
	@$(call check_env_file)
	@$(UV) run automagik-tools serve --tool $(TOOL) --transport stdio
```

#### `make new-tool`
```makefile
new-tool: ## 🔧 Create new tool interactively
	$(call print_status,Creating new tool...)
	@$(UV) run python scripts/create_tool.py
	$(call print_success,Tool created successfully!)
```

#### `make test-tool TOOL=toolname`
```makefile
test-tool: ## 🧪 Test specific tool (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make test-tool TOOL=<tool-name>); \
		exit 1; \
	fi
	@$(UV) run pytest tests/tools/test_$(TOOL).py -v
```

#### `make validate-tool TOOL=toolname`
```makefile
validate-tool: ## ✅ Validate tool compliance (use TOOL=name)
	@if [ -z "$(TOOL)" ]; then \
		$(call print_error,Usage: make validate-tool TOOL=<tool-name>); \
		exit 1; \
	fi
	@$(UV) run python scripts/validate_tool.py $(TOOL)
```

### Story 2.2: Development Server with Hot-Reload
**Priority**: Medium | **Effort**: 6 hours

**Technical Requirements**:
```makefile
dev-server: ## 🔥 Start development server with hot-reload
	$(call print_status,Starting development server with hot-reload...)
	@$(UV) run watchmedo auto-restart \
		--directory automagik_tools \
		--pattern "*.py" \
		--recursive \
		-- make serve-all HOST=127.0.0.1 PORT=8000
```

### Story 2.3: Tool Validation Framework
**Priority**: Medium | **Effort**: 8 hours

**Implementation Specifications**:
- MCP protocol compliance checking
- OpenAPI specification validation (for API tools)
- Security scanning for configurations
- Performance benchmarking

**Required Script**: `scripts/validate_tool.py`
```python
def validate_tool(tool_name: str) -> ValidationResult:
    """Comprehensive tool validation"""
    results = ValidationResult()
    
    # Check MCP compliance
    results.mcp_compliance = validate_mcp_protocol(tool_name)
    
    # Check OpenAPI if applicable
    if has_openapi_spec(tool_name):
        results.openapi_valid = validate_openapi_spec(tool_name)
    
    # Security checks
    results.security_scan = scan_security_issues(tool_name)
    
    # Performance checks
    results.performance = benchmark_tool(tool_name)
    
    return results
```

---

## 🎯 Epic 3: Deployment & Distribution

**Objective**: Enable one-click deployment of MCP tools to production environments

### Story 3.1: SSE Server Deployment
**Priority**: High | **Effort**: 10 hours

**Technical Requirements**:
- Docker containerization for SSE servers
- Cloud provider templates (Railway, Fly.io, Render, Vercel)
- Environment configuration management
- SSL/TLS automation

**Implementation Details**:
```makefile
deploy-sse: ## 🚀 Deploy SSE server to cloud
	$(call print_status,Deploying SSE server...)
	@if [ -z "$(PROVIDER)" ]; then \
		echo "Available providers: railway, fly, render, vercel"; \
		read -p "Choose provider: " PROVIDER; \
	fi
	@$(UV) run python scripts/deploy_sse.py --provider $(PROVIDER)
```

**Required Files**:
- `Dockerfile.sse` - SSE server container
- `railway.json` - Railway deployment config
- `fly.toml` - Fly.io deployment config
- `render.yaml` - Render deployment config

### Story 3.2: Multi-Cloud Deployment Templates
**Priority**: Medium | **Effort**: 12 hours

**Deployment Matrix**:
```
Provider      | SSE Server | Multi-Tool | Auth | SSL | Auto-Scale
--------------|------------|------------|------|-----|------------
Railway       | ✅         | ✅         | ✅   | ✅  | ✅
AWS App Runner| ✅         | ✅         | ✅   | ✅  | ✅
AWS ECS       | ✅         | ✅         | ✅   | ✅  | ✅
Google Cloud Run| ✅       | ✅         | ✅   | ✅  | ✅
Google GKE    | ✅         | ✅         | ✅   | ✅  | ✅
Render        | ✅         | ✅         | ✅   | ✅  | ✅
Docker Local  | ✅         | ✅         | ✅   | ❌  | ❌
```

---

## 🎯 Epic 4: Documentation & User Experience

### Story 4.1: User-Specific Documentation
**Priority**: High | **Effort**: 8 hours

**Documentation Structure**:
```
docs/
├── end-users/
│   ├── quick-start.md           # 2-minute integration guide
│   ├── claude-integration.md    # Claude Desktop specific
│   ├── cursor-integration.md    # Cursor specific
│   ├── troubleshooting.md       # Common issues
│   └── configuration-examples.md # Ready-to-paste configs
├── developers/
│   ├── getting-started.md       # Development setup
│   ├── creating-tools.md        # Tool development guide
│   ├── testing-guide.md         # Testing strategies
│   ├── deployment-guide.md      # Deployment options
│   └── api-reference.md         # Technical API docs
└── deployment/
    ├── docker.md               # Docker deployment
    ├── cloud-providers.md      # Cloud deployment guides
    └── ssl-setup.md            # SSL/TLS configuration
```

---

## 🧪 Testing Strategy

### End User Experience Testing
```bash
# Test uvx workflow
uvx automagik-tools list
uvx automagik-tools serve --tool evolution-api --transport stdio
uvx automagik-tools serve --tool automagik-agents --transport sse --port 8080
```

### Developer Workflow Testing
```bash
# Test make workflow
make install
make new-tool
make serve TOOL=my-new-tool
make test-tool TOOL=my-new-tool
make validate-tool TOOL=my-new-tool
make deploy-sse PROVIDER=railway
```

### Integration Testing
- MCP client compatibility (Claude Desktop, Cursor, Continue)
- Transport method validation (stdio, SSE, HTTP)
- Cloud deployment verification
- Performance benchmarking

---

## 📈 Success Metrics

### End User KPIs
- **Time to Integration**: < 2 minutes from discovery to working MCP tool
- **Success Rate**: > 95% first-time setup success
- **Support Tickets**: < 5% of users need help

### Developer KPIs
- **Tool Creation Time**: < 10 minutes for new tool from template
- **Development Velocity**: Hot-reload working in < 30 seconds
- **Deployment Success**: > 98% successful cloud deployments

### Platform KPIs
- **Tool Discovery**: All tools auto-discovered and servable
- **Transport Compatibility**: 100% support for stdio, SSE, HTTP
- **Documentation Coverage**: 100% of features documented with examples

---

## 🚀 Implementation Timeline

### Phase 1: Critical Path (Week 1)
1. Update documentation to use uvx commands
2. Implement generic `serve` command for all tools
3. Add missing make commands (`serve`, `new-tool`, `test-tool`)

### Phase 2: Developer Experience (Week 2)
1. Hot-reload development server
2. Tool validation framework
3. Enhanced testing commands

### Phase 3: Deployment (Week 3)
1. SSE server deployment automation
2. Cloud provider templates
3. Docker containerization

### Phase 4: Documentation & Polish (Week 4)
1. User-specific documentation
2. Video tutorials and examples
3. Performance optimization

---

## 🔧 Technical Dependencies

### Required Scripts
- [ ] `scripts/validate_tool.py` - Tool validation framework
- [ ] `scripts/deploy_sse.py` - SSE deployment automation
- [ ] `scripts/benchmark_tool.py` - Performance testing

### Infrastructure Requirements
- [ ] Docker templates for containerization
- [ ] Cloud provider deployment configs
- [ ] SSL/TLS certificate automation
- [ ] Monitoring and logging setup

### Testing Infrastructure
- [ ] MCP protocol compliance tests
- [ ] Cross-platform uvx testing
- [ ] Cloud deployment validation
- [ ] Performance benchmarking suite

---

## 📋 Team Assignment Recommendations

### Planning Team
- Epic prioritization and timeline refinement
- User story breakdown and estimation
- Cross-team coordination and dependencies

### Architecture Team
- Transport layer design for universal serving
- Deployment architecture for multi-cloud
- Tool validation framework design
- Performance optimization strategy

### Implementation Team
- Make command implementation
- CLI enhancement for universal serving
- Hot-reload development server
- Cloud deployment scripts

### Code Review Team
- Makefile command validation
- CLI interface consistency
- Error handling and user experience
- Security review for deployment configs

### Testing Team
- End-to-end user workflow testing
- MCP client compatibility testing
- Cloud deployment validation
- Performance benchmarking

### Documentation Team
- User-specific documentation creation
- Video tutorial production
- Configuration example validation
- Troubleshooting guide development

---

## ⚠️ Risk Assessment

### High Risk
- **uvx Dependency**: If uvx has issues, end user experience breaks
- **MCP Protocol Changes**: Breaking changes could affect all tools
- **Cloud Provider Changes**: Deployment templates may become outdated

### Medium Risk
- **Tool Discovery Complexity**: Auto-discovery may fail for complex tools
- **Transport Method Support**: Some tools may not support all transports

### Mitigation Strategies
- Comprehensive testing across all uvx versions
- MCP protocol version compatibility checking
- Regular cloud provider template updates
- Fallback mechanisms for tool discovery

---

**This PRD provides comprehensive technical specifications for specialized agent teams to implement the dual-path user experience for AutoMagik Tools.** 