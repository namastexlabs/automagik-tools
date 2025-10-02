"""Basic tests for all tools to improve coverage"""

from automagik_tools.cli import discover_tools
import pytest


class TestAllToolsMetadata:
    """Test that all tools have proper metadata"""

    def test_all_tools_have_metadata_function(self):
        """Test that all tools have get_metadata function"""
        tools = discover_tools()
        
        for tool_name, tool_info in tools.items():
            module = tool_info["module"]
            
            # Every tool must have get_metadata
            assert hasattr(module, "get_metadata")
            
            # Call it and verify structure
            metadata = module.get_metadata()
            assert isinstance(metadata, dict)
            assert "name" in metadata
            assert len(metadata["name"]) > 0

    def test_all_tools_have_config_class(self):
        """Test that all tools have get_config_class function"""
        tools = discover_tools()
        
        for tool_name, tool_info in tools.items():
            module = tool_info["module"]
            
            # Every tool must have get_config_class
            assert hasattr(module, "get_config_class")
            
            # Call it and verify it returns a class
            config_class = module.get_config_class()
            assert config_class is not None

    def test_all_tools_have_create_server(self):
        """Test that all tools have create_server function"""
        tools = discover_tools()
        
        for tool_name, tool_info in tools.items():
            module = tool_info["module"]
            
            # Every tool must have create_server
            assert hasattr(module, "create_server")
            assert callable(module.create_server)


class TestToolModuleStructure:
    """Test tool module structure"""

    def test_tools_are_properly_imported(self):
        """Test that tool modules can be imported"""
        import automagik_tools.tools.evolution_api
        import automagik_tools.tools.omni
        import automagik_tools.tools.wait
        import automagik_tools.tools.spark
        import automagik_tools.tools.genie
        
        # All imports should succeed
        assert automagik_tools.tools.evolution_api is not None
        assert automagik_tools.tools.omni is not None
        assert automagik_tools.tools.wait is not None
        assert automagik_tools.tools.spark is not None
        assert automagik_tools.tools.genie is not None

    def test_tool_configs_are_importable(self):
        """Test that tool config classes can be imported"""
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig
        from automagik_tools.tools.omni.config import OmniConfig
        from automagik_tools.tools.wait.config import WaitConfig
        from automagik_tools.tools.spark.config import SparkConfig
        from automagik_tools.tools.genie.config import GenieConfig
        
        # All config classes should be importable
        assert EvolutionAPIConfig is not None
        assert OmniConfig is not None
        assert WaitConfig is not None
        assert SparkConfig is not None
        assert GenieConfig is not None

    def test_tool_models_exist_where_applicable(self):
        """Test that tool models exist for tools that need them"""
        from automagik_tools.tools.omni import models as omni_models
        from automagik_tools.tools.spark import models as spark_models
        
        # Models modules should exist
        assert omni_models is not None
        assert spark_models is not None
        
        # They should have model classes
        assert hasattr(omni_models, "MessageType")
        assert hasattr(spark_models, "TaskStatus")


class TestToolClients:
    """Test tool client classes"""

    def test_evolution_client_import(self):
        """Test that Evolution API client can be imported"""
        from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
        
        assert EvolutionAPIClient is not None

    def test_omni_client_import(self):
        """Test that Omni client can be imported"""
        from automagik_tools.tools.omni.client import OmniClient
        
        assert OmniClient is not None

    def test_spark_client_import(self):
        """Test that Spark client can be imported"""
        from automagik_tools.tools.spark.client import SparkClient
        
        assert SparkClient is not None


class TestConfigDefaults:
    """Test config defaults and structure"""

    def test_evolution_config_structure(self):
        """Test Evolution API config structure"""
        from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig
        import os
        
        # Set required fields
        os.environ["EVOLUTION_API_BASE_URL"] = "http://test.com"
        os.environ["EVOLUTION_API_KEY"] = "key"
        
        config = EvolutionAPIConfig()
        
        assert hasattr(config, "base_url")
        assert hasattr(config, "api_key")
        
        # Cleanup
        del os.environ["EVOLUTION_API_BASE_URL"]
        del os.environ["EVOLUTION_API_KEY"]

    def test_omni_config_structure(self):
        """Test Omni config structure"""
        from automagik_tools.tools.omni.config import OmniConfig
        import os
        
        # Set required fields
        os.environ["OMNI_BASE_URL"] = "http://test.com"
        os.environ["OMNI_API_KEY"] = "key"
        
        config = OmniConfig()
        
        assert hasattr(config, "base_url")
        assert hasattr(config, "api_key")
        
        # Cleanup
        del os.environ["OMNI_BASE_URL"]
        del os.environ["OMNI_API_KEY"]

    def test_wait_config_structure(self):
        """Test Wait config structure"""
        from automagik_tools.tools.wait.config import WaitConfig
        
        config = WaitConfig()
        
        # Wait config is simple, just verify it exists
        assert config is not None
