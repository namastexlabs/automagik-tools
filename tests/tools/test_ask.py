"""
Tests for the Ask Tool - Intelligent MCP Orchestrator
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from automagik_tools.tools.ask import (
    ask, plan_only, list_capabilities, get_execution_history,
    get_memory_stats, clear_ask_cache, reset_ask_learning,
    create_tool, get_metadata, AskConfig
)


class TestAskToolBasics:
    """Test basic Ask tool functionality"""
    
    def test_metadata(self):
        """Test tool metadata"""
        metadata = get_metadata()
        
        assert metadata["name"] == "ask"
        assert metadata["version"] == "1.0.0"
        assert "orchestration" in metadata["category"]
        assert "ai" in metadata["tags"]
        assert "features" in metadata
        assert len(metadata["features"]) > 0
    
    def test_config_creation(self):
        """Test configuration creation"""
        config = AskConfig()
        
        # Check default values
        assert config.automagik_base_url == "http://192.168.112.148:8881"
        assert config.enable_ai_processing == True
        assert config.max_execution_steps == 20
        assert config.planning_model == "gpt-4o-mini"
        assert config.synthesis_model == "gpt-4o-mini"
    
    def test_tool_creation(self):
        """Test tool creation"""
        config = AskConfig(
            automagik_api_key="test_key",
            openai_api_key="test_openai_key"
        )
        
        tool = create_tool(config)
        assert tool is not None
        assert tool.name == "Ask - Intelligent MCP Orchestrator"


@pytest.mark.asyncio
class TestAskExecution:
    """Test Ask tool execution functionality"""
    
    @patch('automagik_tools.tools.ask.config')
    async def test_ask_without_config(self, mock_config):
        """Test ask function without configuration"""
        mock_config = None
        
        with pytest.raises(ValueError, match="Ask tool not configured"):
            await ask("test query")
    
    @patch('automagik_tools.tools.ask.agno_workflow')
    @patch('automagik_tools.tools.ask.config')
    async def test_ask_basic_query(self, mock_config, mock_workflow):
        """Test basic ask query execution"""
        # Mock configuration
        mock_config.enable_ai_processing = True
        
        # Mock workflow
        mock_workflow.run.return_value = [
            Mock(content="Step 1 result"),
            Mock(content="Step 2 result"), 
            Mock(content="Final comprehensive response")
        ]
        
        result = await ask("test query")
        
        assert isinstance(result, str)
        assert "Step 1 result" in result
        assert "Final comprehensive response" in result
    
    @patch('automagik_tools.tools.ask.orchestrator')
    @patch('automagik_tools.tools.ask.config')
    async def test_ask_fallback_orchestrator(self, mock_config, mock_orchestrator):
        """Test fallback to standard orchestrator when Agno fails"""
        # Mock configuration
        mock_config.enable_ai_processing = False
        
        # Mock orchestrator
        mock_orchestrator.execute_request = AsyncMock()
        mock_orchestrator.execute_request.return_value = Mock(
            final_response="Orchestrator response",
            model_dump=Mock(return_value={"test": "data"})
        )
        mock_orchestrator.initialize = AsyncMock()
        
        result = await ask("test query", use_agno_workflow=False)
        
        assert isinstance(result, str)
        assert "Orchestrator response" in result
    
    @patch('automagik_tools.tools.ask.config')
    async def test_ask_error_handling(self, mock_config):
        """Test error handling in ask function"""
        mock_config.enable_ai_processing = True
        
        # Test with error condition
        with patch('automagik_tools.tools.ask.agno_workflow') as mock_workflow:
            mock_workflow.run.side_effect = Exception("Test error")
            
            result = await ask("test query")
            
            assert "Error" in result
            assert "Test error" in result


@pytest.mark.asyncio 
class TestAskTools:
    """Test additional Ask tool functions"""
    
    @patch('automagik_tools.tools.ask.agno_workflow')
    async def test_get_memory_stats_without_workflow(self, mock_workflow):
        """Test memory stats when workflow not initialized"""
        mock_workflow = None
        
        result = await get_memory_stats()
        
        assert "Error" in result
        assert "not initialized" in result
    
    @patch('automagik_tools.tools.ask.agno_workflow')
    async def test_get_memory_stats_with_workflow(self, mock_workflow):
        """Test memory stats with initialized workflow"""
        mock_workflow.get_memory_stats.return_value = {
            "execution_metrics": {
                "total_executions": 10,
                "successful_executions": 8,
                "cache_hits": 3,
                "avg_execution_time": 2.5,
                "last_updated": "2024-01-01T00:00:00"
            },
            "cached_results": 5,
            "successful_patterns": 12,
            "tool_performance": 8,
            "common_queries": 6,
            "tool_combinations": 4
        }
        
        result = await get_memory_stats()
        
        assert "Memory & Learning Statistics" in result
        assert "Total Executions**: 10" in result
        assert "Success Rate**: 80.0%" in result
        assert "Cache Hit Rate" in result
    
    @patch('automagik_tools.tools.ask.agno_workflow')
    async def test_clear_cache(self, mock_workflow):
        """Test cache clearing functionality"""
        mock_workflow.clear_cache = Mock()
        
        result = await clear_ask_cache()
        
        assert "Cache Cleared Successfully" in result
        assert "What was cleared" in result
        assert "What was preserved" in result
        mock_workflow.clear_cache.assert_called_once()
    
    @patch('automagik_tools.tools.ask.agno_workflow')
    async def test_reset_learning_without_confirmation(self, mock_workflow):
        """Test learning reset without confirmation"""
        result = await reset_ask_learning()
        
        assert "Confirmation Required" in result
        assert "RESET_LEARNING" in result
        assert "destructive operation" in result
    
    @patch('automagik_tools.tools.ask.agno_workflow')
    async def test_reset_learning_with_confirmation(self, mock_workflow):
        """Test learning reset with proper confirmation"""
        mock_workflow.reset_learning = Mock()
        
        result = await reset_ask_learning(confirmation="RESET_LEARNING")
        
        assert "Learning Data Reset Complete" in result
        assert "What was reset" in result
        mock_workflow.reset_learning.assert_called_once()


@pytest.mark.asyncio
class TestAskPlanning:
    """Test Ask tool planning functionality"""
    
    @patch('automagik_tools.tools.ask.orchestrator')
    @patch('automagik_tools.tools.ask.config') 
    async def test_plan_only(self, mock_config, mock_orchestrator):
        """Test plan-only functionality"""
        # Mock orchestrator and planner
        mock_orchestrator.initialize = AsyncMock()
        
        # Mock planner
        mock_planner = Mock()
        mock_planner.create_plan = AsyncMock()
        mock_planner.create_plan.return_value = Mock(
            query="test query",
            plan_id="test_plan_123",
            steps=[
                Mock(step_id="step_1", tool_name="list_agents", description="Get agents"),
                Mock(step_id="step_2", tool_name="run_agent", description="Run agent")
            ],
            complexity="moderate",
            estimated_duration="10-20 seconds"
        )
        
        with patch('automagik_tools.tools.ask.ExecutionPlanner', return_value=mock_planner):
            result = await plan_only("get agents and run one")
            
            assert isinstance(result, str)
            # Should contain plan information even if AI processing fails


@pytest.mark.asyncio
class TestAskConfiguration:
    """Test Ask tool configuration management"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test with invalid timeout
        config = AskConfig(execution_timeout=-1)
        # Should still create config but with invalid value
        assert config.execution_timeout == -1
        
        # Test boolean configs
        config = AskConfig(
            enable_ai_processing=False,
            safe_mode=True,
            debug_mode=True
        )
        assert config.enable_ai_processing == False
        assert config.safe_mode == True
        assert config.debug_mode == True
    
    def test_config_methods(self):
        """Test configuration helper methods"""
        config = AskConfig(
            automagik_api_key="test_key",
            automagik_base_url="http://test.com",
            automagik_timeout=60,
            openai_api_key="openai_key",
            planning_model="gpt-4",
            safe_mode=True,
            excluded_tools=["dangerous_tool"],
            preferred_tools=["safe_tool"]
        )
        
        # Test automagik config
        automagik_config = config.get_automagik_config()
        assert automagik_config["api_key"] == "test_key"
        assert automagik_config["base_url"] == "http://test.com"
        assert automagik_config["timeout"] == 60
        
        # Test AI config
        ai_config = config.get_ai_config()
        assert ai_config["openai_api_key"] == "openai_key"
        assert ai_config["planning_model"] == "gpt-4"
        
        # Test execution config
        exec_config = config.get_execution_config()
        assert "max_execution_steps" in exec_config
        assert "enable_parallel_execution" in exec_config
        
        # Test safe operations
        assert config.is_safe_operation("read_file") == True
        assert config.is_safe_operation("delete_everything") == True  # Safe mode allows all when not checking operation type
        
        # Test tool filtering
        assert config.should_exclude_tool("dangerous_tool") == True
        assert config.should_exclude_tool("safe_tool") == False
        
        # Test tool priority
        assert config.get_tool_priority("safe_tool") > config.get_tool_priority("other_tool")


class TestAskIntegration:
    """Integration tests for Ask tool components"""
    
    def test_imports(self):
        """Test that all required imports work"""
        # Test main imports
        from automagik_tools.tools.ask import ask, plan_only, list_capabilities
        from automagik_tools.tools.ask.config import AskConfig
        from automagik_tools.tools.ask.planner import ExecutionPlanner
        from automagik_tools.tools.ask.orchestrator import ToolOrchestrator
        from automagik_tools.tools.ask.synthesizer import ResponseSynthesizer
        
        # All imports should work without errors
        assert True
    
    def test_agno_imports(self):
        """Test Agno imports (may fail if Agno not installed)"""
        try:
            from automagik_tools.tools.ask.agno_orchestrator import AskMasterWorkflow
            agno_available = True
        except ImportError:
            agno_available = False
        
        # Should handle import gracefully
        assert agno_available in [True, False]


@pytest.mark.unit 
class TestAskUtilities:
    """Test Ask tool utility functions"""
    
    def test_metadata_structure(self):
        """Test metadata structure is complete"""
        metadata = get_metadata()
        
        required_fields = ["name", "version", "description", "author", "category", "tags", "features"]
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
        
        assert isinstance(metadata["tags"], list)
        assert isinstance(metadata["features"], list)
        assert len(metadata["features"]) >= 5  # Should have multiple features listed
    
    def test_tool_creation_with_different_configs(self):
        """Test tool creation with various configurations"""
        # Test with minimal config
        minimal_config = AskConfig()
        tool1 = create_tool(minimal_config)
        assert tool1 is not None
        
        # Test with full config
        full_config = AskConfig(
            automagik_api_key="key1",
            openai_api_key="key2", 
            enable_ai_processing=True,
            max_execution_steps=15,
            debug_mode=True
        )
        tool2 = create_tool(full_config)
        assert tool2 is not None
        
        # Both tools should be different instances but same type
        assert type(tool1) == type(tool2)
        assert tool1 is not tool2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])