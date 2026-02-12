# YWW-QQBot

## 项目简介

YWW-QQBot 是一个基于 NapCat 的 QQ 机器人项目，用于处理群组消息中的精华消息功能。它提供了一套完整的指令处理框架，方便开发者快速扩展新的功能。

## 功能特性

- **精华消息备份**：自动备份群组中的精华消息，最多保存5份记录
- **手动添加精华**：支持手动将指定消息添加到精华备份中
- **精华消息查看**：支持按日期、QQ号或数量筛选查看精华消息
- **模块化设计**：采用模块化设计，方便开发者快速接入新的指令

## 快速开始

### 环境要求

- Python 3.8+
- NapCat
- Peewee (用于数据库操作)

### 安装依赖

```bash
pip install napcat peewee
```

### 配置与运行

1. 修改 `src/main.py` 中的配置信息：

```python
client = NapCatClient(
    ws_url="ws://127.0.0.1:3000",
    token="your_token"
)
```

2. 运行项目：

```bash
python src/main.py
```

## 项目结构

```
YWW-QQBot/
├── src/                       # 源代码目录
│   ├── __init__.py            # 包初始化文件
│   ├── command_dispatch/      # 命令分发相关模块
│   │   ├── __init__.py        # 子包初始化文件
│   │   ├── command_ctx.py     # 命令上下文
│   │   ├── command_dispatcher.py  # 命令分发器
│   │   └── handler_registry.py    # 处理器注册
│   ├── handlers/              # 命令处理器
│   │   ├── __init__.py        # 子包初始化文件
│   │   ├── base/              # 基础处理器
│   │   │   ├── __init__.py    # 子包初始化文件
│   │   │   ├── command_handler_base.py    # 命令处理器基类
│   │   │   └── command_handler_common.py  # 命令处理器公共模块
│   │   ├── essence/           # 精华消息处理器
│   │   │   ├── __init__.py    # 子包初始化文件
│   │   │   ├── essence_handler.py # 精华消息处理逻辑
│   │   │   └── essence_backup.db  # 精华消息备份数据库
│   │   └── help/              # 帮助命令处理器
│   │       ├── __init__.py    # 子包初始化文件
│   │       └── help_handler.py    # 帮助命令处理逻辑
│   └── main.py                # 主入口文件
├── .gitignore                 # Git 忽略文件
└── README.md                  # 项目说明文档
```

## 如何添加新指令

添加新指令非常简单，只需按照以下步骤操作：

### 1. 创建新的处理器类

在 `handlers` 目录下创建一个新的目录（如果需要），然后创建一个新的处理器文件。处理器类需要继承自 `CommandHandlerBase`。

### 2. 注册处理器

使用 `@register_handler` 装饰器注册处理器，指定分类和聊天类型。

### 3. 添加指令方法

使用 `@CommandHandlerBase.command` 装饰器标记方法为指令处理函数，指定指令名称、使用方法和描述。

### 4. 实现指令逻辑

在指令处理方法中实现具体的业务逻辑。

### 示例

```python
# -*- coding: utf-8 -*-
"""示例处理器模块。"""

from napcat import Text, GroupMessageEvent, PrivateMessageEvent
from handlers.base.command_handler_common import *


@register_handler(category="示例", chat_type="group")
class ExampleHandler(CommandHandlerBase):
    """示例处理器。"""
    
    @CommandHandlerBase.command("hello", 
                               usage="hello",
                               description="打招呼示例指令")
    async def handle_hello(self, event: GroupMessageEvent, args: list):
        """处理打招呼指令。"""
        await event.reply([Text(text="Hello, World!")])
```

### 5. 确保处理器被导入

确保新创建的处理器在项目启动时被导入。可以在 `src/handlers/__init__.py` 中添加导入语句。

## 现有指令说明

### 精华消息相关指令

- **备份精华**：备份当前群聊的所有精华消息，最多保存5份记录
- **添加精华**：将引用的消息添加到当前最新备份的记录中
- **查看精华**：查看精华消息，支持按日期、QQ号或数量筛选，默认显示前10条
  - 格式：`查看精华 [日期/QQ号/数量]`
  - 示例：
    - `查看精华 2025.02.07` - 查看2025年2月7日的精华消息
    - `查看精华 123456789` - 查看QQ号为123456789的用户的精华消息
    - `查看精华 20` - 查看前20条精华消息

## 注意事项

确保 NapCat 服务已经启动并运行在指定的 WebSocket 地址
