import importlib
import os
import sys

from command_dispatch.handler_registry import HandlerRegistry

# 指令缓存单例类
class CommandCache:
    _instance = None
    _commands = {}  # 格式: {command_name: {"usage": "", "description": "", "category": "", "chat_type": ""}}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        if self._initialized:
            return
        
        self._discover_handlers()

        self._commands = {}
        
        for handler_class in HandlerRegistry.get_all_handlers():
            handler = handler_class()
            category = getattr(handler_class, "_category", "通用")
            chat_type = getattr(handler_class, "_chat_type", "both")
            
            # 获取所有方法，检查哪些是命令处理函数
            for attr_name in dir(handler):
                attr = getattr(handler, attr_name)
                if hasattr(attr, "_command_names"):
                    command_names = attr._command_names
                    usage = getattr(attr, "_usage", "")
                    description = getattr(attr, "_description", "")
                    
                    for command_name in command_names:
                        normalized_name = command_name.lower()
                        self._commands[normalized_name] = {
                            "usage": usage,
                            "description": description,
                            "category": category,
                            "chat_type": chat_type
                        }
        
        self._initialized = True
        print(f"指令缓存已初始化，共缓存 {len(self._commands)} 个指令")
    
    def get_all_commands(self):
        if not self._initialized:
            raise Exception("command cache is not initialized")
        return self._commands
    
    def get_commands_by_category(self, category):
        """根据类别获取命令"""
        if not self._initialized:
            raise Exception("command cache is not initialized")
        return {cmd: info for cmd, info in self._commands.items() if info["category"] == category}
    
    def get_categories(self):
        """获取所有命令类别"""
        if not self._initialized:
            raise Exception("command cache is not initialized")
        return set(info["category"] for info in self._commands.values())
    
    def _discover_handlers(self):
        # TODO: 这里为了简单起见，直接假设了 handlers 目录的位置，后续需要修改一下 
        handlers_dir = os.path.join(os.path.dirname(__file__), '..', 'handlers')

        root_dir = os.path.abspath(handlers_dir)

        if root_dir not in sys.path:
            sys.path.append(root_dir)

        for root, dirs, files in os.walk(handlers_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    try:
                        file_abs_path = os.path.abspath(os.path.join(root, file))
                        relative_path = os.path.relpath(file_abs_path, root_dir)
                        module_path = relative_path.replace('.py', '').replace(os.sep, '.')
                        
                        if module_path.startswith('.'):
                            module_path = module_path[1:]

                        importlib.import_module(module_path)
                    except Exception as e:
                        print(f"导入文件 {os.path.join(root, file)} 时出错: {e}")


# 上下文单例类，用于管理user_info和client实例
class CommandContext:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, user_info, client=None):
        self._user_info = user_info
        self._client = client
        self._initialized = True
    
    def cleanup(self):
        self._user_info = None
        self._client = None
        self._initialized = False
    
    @property
    def user_info(self):
        if not self._initialized:
            raise Exception("command context is not initialized")
        return self._user_info
    
    @property
    def client(self):
        if not self._initialized:
            raise Exception("command context is not initialized")
        return self._client
    
    def is_initialized(self):
        return self._initialized