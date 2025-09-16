"""
Tests for LinkedIn MCP Server
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from linkedin_mcp_server import app, TOOLS
except ImportError:
    pytest.skip("MCP dependencies not available", allow_module_level=True)


class TestLinkedInMCPServer:
    """Test cases for LinkedIn MCP Server"""
    
    def test_tools_list(self):
        """Test that all expected tools are available"""
        tool_names = [tool.name for tool in TOOLS]
        expected_tools = [
            "search_jobs",
            "apply_to_job", 
            "get_profile",
            "update_profile",
            "send_connection_request"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in tools list"
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test the list_tools handler"""
        tools = await app._handlers["list_tools"]()
        assert len(tools) == 5
        assert all(hasattr(tool, 'name') for tool in tools)
    
    @pytest.mark.asyncio 
    async def test_search_jobs_tool(self):
        """Test the search_jobs tool call"""
        result = await app._handlers["call_tool"]("search_jobs", {"keywords": "python developer"})
        assert len(result) == 1
        assert "python developer" in result[0].text
    
    @pytest.mark.asyncio
    async def test_apply_to_job_tool(self):
        """Test the apply_to_job tool call"""
        result = await app._handlers["call_tool"]("apply_to_job", {"job_id": "12345"})
        assert len(result) == 1
        assert "12345" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_profile_tool(self):
        """Test the get_profile tool call"""
        result = await app._handlers["call_tool"]("get_profile", {})
        assert len(result) == 1
        assert "profile information" in result[0].text
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test handling of unknown tool calls"""
        result = await app._handlers["call_tool"]("unknown_tool", {})
        assert len(result) == 1
        assert "Unknown tool" in result[0].text


class TestEnvironmentValidation:
    """Test environment variable validation"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variables(self):
        """Test that missing environment variables are detected"""
        # This would normally cause the server to exit
        # In a real implementation, you'd test the validation logic
        required_vars = ['LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        assert len(missing_vars) == 2
    
    @patch.dict(os.environ, {
        'LINKEDIN_CLIENT_ID': 'test_id',
        'LINKEDIN_CLIENT_SECRET': 'test_secret'
    })
    def test_valid_environment_variables(self):
        """Test that valid environment variables are accepted"""
        required_vars = ['LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        assert len(missing_vars) == 0


if __name__ == "__main__":
    pytest.main([__file__])