from handlers.base.command_handler_common import *

from napcat import Text, GroupMessageEvent, PrivateMessageEvent

# 帮助指令处理器
@register_handler(category="帮助", chat_type="both")
class HelpHandler(CommandHandlerBase):
    def __init__(self):
        super().__init__()

    @CommandHandlerBase.command("help", 
                               usage="help [类别]",
                               description="查看帮助信息，可以指定类别查询特定类别的指令")
    async def _handle_help(self, event, args: list):
        # 使用CommandCache单例获取所有指令
        from command_dispatch.command_ctx import CommandCache
        command_cache = CommandCache()
        
        try:
            all_commands = command_cache.get_all_commands()
            
            # 确定当前聊天类型
            if isinstance(event, GroupMessageEvent):
                current_chat_type = "group"
            elif isinstance(event, PrivateMessageEvent):
                current_chat_type = "private"
            
            # 过滤出当前聊天类型可用的命令
            available_commands = {}
            for cmd, info in all_commands.items():
                chat_type = info["chat_type"]
                if chat_type == "both" or chat_type == current_chat_type:
                    if info["category"] not in available_commands:
                        available_commands[info["category"]] = []
                    available_commands[info["category"]].append((cmd, info))
            
            # 处理类别查询
            if args:
                query_category = args[0]
                if query_category in available_commands:
                    help_text = f"{query_category} 类指令：\n"
                    for cmd, info in sorted(available_commands[query_category]):
                        help_text += f"- {cmd}"
                        if info["usage"]:
                            help_text += f" (用法：{info['usage']})"
                        if info["description"]:
                            help_text += f"：{info['description']}"
                        help_text += "\n"
                else:
                    help_text = f"未找到类别：{query_category}\n"
                    help_text += "可用类别：\n"
                    for category in sorted(available_commands.keys()):
                        help_text += f"- {category}\n"
            else:
                # 生成所有类别的帮助信息
                help_text = "可用指令：\n"
                for category in sorted(available_commands.keys()):
                    help_text += f"\n【{category}】\n"
                    for cmd, info in sorted(available_commands[category]):
                        help_text += f"- {cmd}"
                        if info["usage"]:
                            help_text += f" (用法：{info['usage']})"
                        if info["description"]:
                            help_text += f"：{info['description']}"
                        help_text += "\n"
        except Exception as e:
            help_text = f"获取帮助信息时出错: {e}\n"
        
        await event.reply([Text(text=help_text)])