# -*- coding: utf-8 -*-
"""Command handler base module.

This module provides the base class for command handlers.
"""

from napcat import GroupMessageEvent, PrivateMessageEvent


class CommandHandlerBase:
    """指令处理器基类。
    
    所有指令处理器都应该继承自这个类，它提供了注册和处理指令的基本功能。
    """
    
    def __init__(self):
        """初始化指令处理器。"""
        self._command_handlers = {}
        self._register_commands()
    
    def _register_commands(self):
        """注册所有标记为指令的方法。"""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_command_names'):
                for command_name in attr._command_names:
                    normalized_name = command_name.lower()
                    self._command_handlers[normalized_name] = attr
    
    @classmethod
    def command(cls, *command_names, usage="", description=""):
        """装饰器，用于标记方法为指令处理函数。
        
        Args:
            *command_names: 指令名称列表
            usage: 指令使用方法
            description: 指令描述
            
        Returns:
            装饰后的函数
        """
        def decorator(func):
            func._command_names = command_names
            func._usage = usage
            func._description = description
            return func
        return decorator
    
    async def handle(self, event, command: str, args: list):
        """处理指令。
        
        Args:
            event: 消息事件
            command: 指令名称
            args: 指令参数列表
            
        Returns:
            bool: 是否成功处理指令
        """
        # 检查事件类型是否支持
        if not isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
            return False
            
        normalized_command = command.lower()
        if normalized_command in self._command_handlers:
            handler_func = self._command_handlers[normalized_command]
            await handler_func(event, args)
            return True
        return False