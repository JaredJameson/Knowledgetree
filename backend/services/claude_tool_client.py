"""
KnowledgeTree - Anthropic Tool Use Client
Client for Claude API with tool calling support
"""

import json
from typing import Dict, Any, List, Callable, Optional, Union
from anthropic import Anthropic
from datetime import datetime

from core.config import settings


class AnthropicToolClient:
    """
    Client for Anthropic Claude API with tool calling support
    
    Enables Claude 3.5 Sonnet to call external tools and functions,
    handling multi-turn conversations for tool use.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic client
        
        Args:
            api_key: Anthropic API key (defaults to settings.ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = Anthropic(api_key=self.api_key)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.tool_functions: Dict[str, Callable] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function: Callable
    ):
        """
        Register a tool for Claude to call
        
        Args:
            name: Tool name (must match function name)
            description: Tool description for Claude
            input_schema: JSON Schema for tool input
            function: Async function to execute
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema
        }
        self.tool_functions[name] = function
    
    def get_tools_for_api(self) -> List[Dict[str, Any]]:
        """Get tools in format expected by Anthropic API"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for tool in self.tools.values()
        ]
    
    async def execute_with_tools(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_turns: int = 10,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute Claude with tool calling
        
        Handles multi-turn conversations where Claude can call tools
        and receive results before generating final response.
        
        Args:
            user_message: User's message to Claude
            system_prompt: Optional system prompt
            max_turns: Maximum tool use turns (prevents infinite loops)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            context: Additional context to pass to tools
        
        Returns:
            Dict containing:
                - response: Final text response from Claude
                - tool_calls: List of tool calls made
                - tool_results: List of tool results
                - turns: Number of conversation turns
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            # System prompts are handled differently in Anthropic API
            pass  # Will be passed directly to API
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        tool_calls = []
        tool_results = []
        
        for turn in range(max_turns):
            try:
                # Call Claude API
                response = self.client.messages.create(
                    model=model,
                    system=system_prompt,
                    messages=messages,
                    tools=self.get_tools_for_api() if self.tools else None,
                    max_tokens=max_tokens
                )
            except Exception as e:
                return {
                    "response": None,
                    "error": str(e),
                    "tool_calls": tool_calls,
                    "tool_results": tool_results,
                    "turns": turn + 1
                }
            
            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Extract tool use blocks
                tool_use_blocks = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]
                
                # Add assistant response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Execute each tool
                current_tool_results = []
                for block in tool_use_blocks:
                    tool_call_info = {
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    tool_calls.append(tool_call_info)
                    
                    # Execute tool function
                    if block.name in self.tool_functions:
                        try:
                            # Merge context with tool input
                            tool_input = {**block.input}
                            if context:
                                tool_input["_context"] = context
                            
                            # Execute tool function
                            result = await self.tool_functions[block.name](**tool_input)
                            
                            # Handle different result types
                            if isinstance(result, dict):
                                result_str = json.dumps(result)
                            elif isinstance(result, str):
                                result_str = result
                            else:
                                result_str = str(result)
                            
                            tool_result_info = {
                                "tool_use_id": block.id,
                                "content": result_str,
                                "status": "success"
                            }
                            current_tool_results.append(tool_result_info)
                            tool_results.append(tool_result_info)
                            
                        except Exception as e:
                            error_result = {
                                "tool_use_id": block.id,
                                "content": json.dumps({"error": str(e)}),
                                "status": "error"
                            }
                            current_tool_results.append(error_result)
                            tool_results.append(error_result)
                    else:
                        # Tool not found
                        error_result = {
                            "tool_use_id": block.id,
                            "content": json.dumps({"error": f"Tool '{block.name}' not found"}),
                            "status": "error"
                        }
                        current_tool_results.append(error_result)
                        tool_results.append(error_result)
                
                # Add tool results message
                messages.append({
                    "role": "user",
                    "content": current_tool_results
                })
                
            else:
                # Claude is done, return final response
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                
                return {
                    "response": final_text,
                    "tool_calls": tool_calls,
                    "tool_results": tool_results,
                    "turns": turn + 1,
                    "stop_reason": response.stop_reason
                }
        
        # Max turns exceeded
        return {
            "response": "Max tool use turns exceeded",
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "turns": max_turns,
            "error": "max_turns_exceeded"
        }
    
    async def execute_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096
    ) -> str:
        """
        Execute Claude without tool calling (simple chat)
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Claude model
            max_tokens: Maximum tokens
        
        Returns:
            Claude's text response
        """
        try:
            response = self.client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            
            text = ""
            for block in response.content:
                if block.type == "text":
                    text += block.text
            
            return text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


# ============================================================================
# Tool Registry and Common Tools
# ============================================================================

class ToolRegistry:
    """Registry for managing available tools"""
    
    _instance = None
    _tools: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function: Callable
    ):
        """Register a tool"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "function": function
        }
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools"""
        return self._tools.copy()
    
    async def execute_tool(
        self,
        name: str,
        input_data: Dict[str, Any]
    ) -> Any:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        return await tool["function"](**input_data)


# Global tool registry instance
tool_registry = ToolRegistry.get_instance()
