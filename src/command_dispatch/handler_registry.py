# 全局处理器注册器
class HandlerRegistry:
    _instance = None
    _handlers = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, handler_class, category="通用", chat_type="both"):
        # 设置处理器的元信息
        handler_class._category = category
        handler_class._chat_type = chat_type
        
        if handler_class not in cls._handlers:
            cls._handlers.append(handler_class)
    
    @classmethod
    def get_all_handlers(cls):
        return cls._handlers
    
# 装饰器
def register_handler(category="通用", chat_type="both"):
    def decorator(handler_class):
        HandlerRegistry.register(handler_class, category, chat_type)
        return handler_class
    return decorator