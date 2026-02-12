from napcat import GroupMessageEvent, PrivateMessageEvent
from napcat import At, Text
from command_dispatch.handler_registry import HandlerRegistry
from command_dispatch.command_ctx import CommandCache, CommandContext

# 指令分发器
class CommandDispatcher:
    def __init__(self):
        self._handler_instances = {}
        self._all_commands = None
        
        # 初始化指令缓存
        command_cache = CommandCache()
        command_cache.initialize()

    
    def _extract_command_and_args(self, message_list, is_private=False):
        text_content = []
        
        if is_private:
            # 私聊消息：直接提取所有文本内容
            for msg_detail in message_list:
                if isinstance(msg_detail, Text):
                    text_content.append(msg_detail.text)
        else:
            # 群消息：找到@之后的文本内容
            after_at = False
            for msg_detail in message_list:
                if isinstance(msg_detail, At):
                    if str(msg_detail.qq) == str(CommandContext().user_info["user_id"]):
                        after_at = True
                elif isinstance(msg_detail, Text) and after_at:
                    text_content.append(msg_detail.text)
        
        # 合并文本内容并分割指令和参数
        full_text = ''.join(text_content).strip()
        if not full_text:
            return None, []
        
        parts = full_text.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    async def _try_handle_command_msg(self, event):
        # 检查消息类型并确定是否需要@检查
        if isinstance(event, GroupMessageEvent):
            # 群消息需要检查是否@了机器人
            has_at = any(isinstance(msg, At) and str(msg.qq) == str(CommandContext().user_info["user_id"]) 
                        for msg in event.message)
            
            if not has_at:
                return False
        elif isinstance(event, PrivateMessageEvent):
            # 私聊消息直接处理，不需要@检查
            pass
        else:
            # 不支持的事件类型
            return False
        
        # 提取指令和参数
        is_private = isinstance(event, PrivateMessageEvent)
        command, args = self._extract_command_and_args(event.message, is_private)
        if not command:
            return False
        
        # 尝试使用所有注册的处理器处理指令
        for handler_class in HandlerRegistry.get_all_handlers():
            # 检查处理器的聊天类型是否与当前事件匹配
            handler_chat_type = getattr(handler_class, "_chat_type", "both")
            if handler_chat_type == "group" and not isinstance(event, GroupMessageEvent):
                continue
            if handler_chat_type == "private" and not isinstance(event, PrivateMessageEvent):
                continue
            
            handler_key = handler_class.__name__
            if handler_key not in self._handler_instances:
                self._handler_instances[handler_key] = handler_class()
            
            handler = self._handler_instances[handler_key]
            
            if await handler.handle(event, command, args):
                return True
        
        return False