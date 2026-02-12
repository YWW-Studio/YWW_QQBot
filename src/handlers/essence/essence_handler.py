# -*- coding: utf-8 -*-
"""Essence message handler module.

This module provides functionality for backing up, adding, and viewing essence messages in groups.
"""

import os
import datetime
import ast
from peewee import *
from napcat import Text, Reply, GroupMessageEvent, NapCatClient
from handlers.base.command_handler_common import *


db_path = os.path.join(os.path.dirname(__file__), "essence_backup.db")
db = SqliteDatabase(db_path)

# 表基类
class BaseModel(Model):
    class Meta:
        database = db

# 备份记录表
class BackupRecord(BaseModel):
    group_id = CharField()
    backup_time = DateTimeField(default=datetime.datetime.now)
    is_current = IntegerField(default=0)

# 精华消息表
class EssenceMessage(BaseModel):
    backup = ForeignKeyField(BackupRecord, backref='messages')
    group_id = CharField()
    message_id = CharField()
    message_seq = CharField()
    sender_id = CharField()
    sender_nick = CharField()
    operator_id = CharField()
    operator_nick = CharField()
    operator_time = BigIntegerField()
    content = TextField()

@register_handler(category="精华", chat_type="group")
class EssenceHandler(CommandHandlerBase):
    """精华消息处理器。
    
    提供备份、添加和查看精华消息的功能。
    """
    
    def __init__(self):
        super().__init__()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库，创建必要的表。"""
        with db:
            db.create_tables([BackupRecord, EssenceMessage])
    
    @CommandHandlerBase.command("备份精华", 
                               usage="备份精华",
                               description="备份当前群聊的所有精华消息，最多保存5份记录")
    async def handle_essence_backup(self, event: GroupMessageEvent, args: list):
        """处理备份精华消息命令。"""
        group_id = event.group_id
        await event.reply([Text(text="正在备份精华消息...")])
        
        try:
            # 获取当前群聊的精华消息列表
            client: NapCatClient = CommandContext().client
            essence_list = await client.get_essence_msg_list(group_id=group_id)
            
            if not essence_list:
                await event.reply([Text(text="当前群聊没有精华消息")])
                return
            
            # 开始事务
            with db.atomic():
                self._cleanup_old_backups(group_id)
                current_backup = self._get_current_backup(group_id)
                new_backup = self._create_new_backup(group_id)
                essence_msg_ids = self._insert_current_essence_messages(
                    new_backup, group_id, essence_list
                )
                self._insert_previous_essence_messages(
                    new_backup, group_id, current_backup, essence_msg_ids
                )
            
            await event.reply([Text(text=f"精华消息备份完成，共备份 {len(essence_list)} 条消息")])
        except Exception as e:
            await event.reply([Text(text=f"备份精华消息失败：{str(e)}")])
    
    def _cleanup_old_backups(self, group_id: str):
        """清理旧的备份记录，最多保留5份。"""
        backup_count = BackupRecord.select().where(
            BackupRecord.group_id == group_id
        ).count()
        
        # 如果备份数量超过4（即第5份），删除最早的备份
        if backup_count >= 5:
            # 获取最早的备份记录
            oldest_backup = BackupRecord.select().where(
                BackupRecord.group_id == group_id
            ).order_by(BackupRecord.backup_time.asc()).first()
            if oldest_backup:
                # 删除关联的精华消息
                EssenceMessage.delete().where(
                    EssenceMessage.backup == oldest_backup
                ).execute()
                # 删除备份记录
                oldest_backup.delete_instance()
    
    def _get_current_backup(self, group_id: str):
        """获取当前最新的备份记录。"""
        return BackupRecord.select().where(
            (BackupRecord.group_id == group_id) & (BackupRecord.is_current == 1)
        ).order_by(BackupRecord.backup_time.desc()).first()
    
    def _create_new_backup(self, group_id: str):
        """创建新的备份记录。"""
        # 将所有备份记录标记为非当前
        BackupRecord.update(is_current=0).where(
            BackupRecord.group_id == group_id
        ).execute()
        
        # 创建新的备份记录
        return BackupRecord.create(
            group_id=group_id,
            backup_time=datetime.datetime.now(),
            is_current=1
        )
    
    def _insert_current_essence_messages(self, backup, group_id: str, essence_list: list):
        """插入当前精华列表中的消息。"""
        essence_msg_ids = set()
        
        for msg in essence_list:
            message_id = str(msg.get("message_id", ""))
            essence_msg_ids.add(message_id)
            
            EssenceMessage.create(
                backup=backup,
                group_id=group_id,
                message_id=message_id,
                message_seq=msg.get("msg_seq", ""),
                sender_id=msg.get("sender_id", ""),
                sender_nick=msg.get("sender_nick", ""),
                operator_id=msg.get("operator_id", ""),
                operator_nick=msg.get("operator_nick", ""),
                operator_time=msg.get("operator_time", 0),
                content=msg.get("content", ""),
            )
        
        return essence_msg_ids
    
    def _insert_previous_essence_messages(self, backup, group_id: str, current_backup, essence_msg_ids: set):
        """插入之前备份中存在但当前精华列表不存在的消息。"""
        if not current_backup:
            return
        
        # 获取当前备份中的所有精华消息
        current_backup_messages = EssenceMessage.select().where(
            EssenceMessage.backup == current_backup
        )
        
        # 插入当前备份中存在但当前精华列表不存在的消息
        for msg in current_backup_messages:
            if msg.message_id not in essence_msg_ids:
                EssenceMessage.create(
                    backup=backup,
                    group_id=group_id,
                    message_id=msg.message_id,
                    message_seq=msg.message_seq,
                    sender_id=msg.sender_id,
                    sender_nick=msg.sender_nick,
                    operator_id=msg.operator_id,
                    operator_nick=msg.operator_nick,
                    operator_time=msg.operator_time,
                    content=msg.content,
                )
    


    @CommandHandlerBase.command("添加精华", 
                               usage="添加精华",
                               description="将指定消息添加到当前最新备份的记录中")
    async def handle_essence_add(self, event : GroupMessageEvent, args: list):
        message_id = next((msg.id for msg in event.message if isinstance(msg, Reply)), None)
        if message_id is None:
            await event.reply([Text(text="请引用要添加的消息并@我~")])
            return
        
        group_id = event.group_id
        try:
            # 获取当前最新的备份记录
            current_backup = BackupRecord.select().where(
                (BackupRecord.group_id == group_id) & (BackupRecord.is_current == 1)
            ).order_by(BackupRecord.backup_time.desc()).first()
            
            if not current_backup:
                await event.reply([Text(text="没有找到当前备份记录，请先执行备份精华命令")])
                return
            
            # 获取消息详情
            client:NapCatClient = CommandContext().client
            msg_info = await client.get_msg(message_id=message_id)
            
            # 插入到精华消息表
            EssenceMessage.create(
                backup=current_backup,
                group_id=group_id,
                message_id=msg_info.get("message_id", ""),
                message_seq=msg_info.get("message_seq", ""),
                sender_id=msg_info.get("sender").get("user_id", ""),
                sender_nick=msg_info.get("sender").get("nickname", ""),
                operator_id=msg_info.get("sender").get("user_id", ""),  # 操作者默认为消息发送者
                operator_nick=msg_info.get("sender").get("nickname", ""),  # 操作者昵称默认为消息发送者昵称
                operator_time=int(datetime.datetime.now().timestamp()),
                content=msg_info.get("message", ""),
            )
            
            await event.reply([Text(text="消息已添加到精华备份中")])
        except Exception as e:
            await event.reply([Text(text=f"添加精华消息失败：{str(e)}")])
    

    @CommandHandlerBase.command("查看精华", 
                               usage="查看精华 [日期/QQ号/数量]",
                               description="查看精华消息，支持按日期、QQ号或数量筛选，默认显示前10条")
    async def handle_essence_list(self, event : GroupMessageEvent, args: list):
        """处理查看精华消息命令。"""
        group_id = event.group_id
        client:NapCatClient = CommandContext().client
        
        try:
            # 获取当前最新的备份记录
            current_backup = self._get_current_backup(group_id)
            
            if not current_backup:
                await event.reply([Text(text="没有找到当前备份记录，请先执行备份精华命令")])
                return
            
            # 构建查询条件
            query = EssenceMessage.select().where(
                (EssenceMessage.backup == current_backup) & 
                (EssenceMessage.group_id == group_id)
            )
            
            # 处理参数并更新查询
            query, limit_count = self._process_query_params(query, args)
            
            # 按时间倒序排列，最新的在前
            query = query.order_by(EssenceMessage.operator_time.desc())
            if limit_count is not None:
                query = query.limit(limit_count)
            
            # 执行查询
            messages = list(query)
            
            if not messages:
                await event.reply([Text(text="没有找到匹配的精华消息")])
                return
            
            # 准备转发消息格式
            forward_msgs = self._prepare_forward_messages(messages)
            
            # 发送转发消息
            await client.send_group_forward_msg(group_id=group_id, messages=forward_msgs)
            
        except Exception as e:
            await event.reply([Text(text=f"查看精华消息失败：{str(e)}")])
    
    def _process_query_params(self, query, args: list):
        """处理查询参数，更新查询条件和限制条数。"""
        # 设置默认显示条数
        limit_count = 10
        
        if not args:
            return query, limit_count
        
        # 处理第一个参数
        param = args[0]
        
        # 检查参数类型：日期、QQ号、还是数字
        if param.count(".") == 2:
            # 完整日期格式 (2025.02.07)
            query = self._process_date_param(query, param)
            limit_count = 100
        elif param.count(".") == 1:
            # 年月格式 (2025.02)
            query = self._process_year_month_param(query, param)
            limit_count = 100
        elif param.isdigit() and len(param) == 4:
            # 仅年份格式 (2025)
            query = self._process_year_param(query, param)
            limit_count = 100
        elif param.isdigit() and 1 <= int(param) <= 100:
            # 单个数字参数，按条数查询
            limit_count = int(param)
        else:
            # QQ号
            query = query.where(EssenceMessage.sender_id == param)
            limit_count = 100
        
        # 处理第二个参数（数量）
        if len(args) >= 2:
            limit_count = self._process_limit_param(args[1], limit_count)
        
        return query, limit_count
    
    def _process_date_param(self, query, date_param: str):
        """处理日期参数。"""
        date_str = date_param.replace(".", "-")
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        # 精确到天的查询
        query = query.where(
            fn.DATE(fn.datetime(EssenceMessage.operator_time, 'unixepoch')) == target_date
        )
        return query
    
    def _process_year_month_param(self, query, year_month_param: str):
        """处理年月参数。"""
        year_month_str = year_month_param.replace(".", "-")
        year_month = datetime.datetime.strptime(year_month_str, "%Y-%m")
        # 计算月份的开始和结束时间戳
        start_timestamp = int(datetime.datetime(year_month.year, year_month.month, 1).timestamp())
        if year_month.month == 12:
            end_timestamp = int(datetime.datetime(year_month.year + 1, 1, 1, 23, 59, 59).timestamp())
        else:
            end_timestamp = int(datetime.datetime(year_month.year, year_month.month + 1, 1, 23, 59, 59).timestamp())
        # 按月查询
        query = query.where(
            (EssenceMessage.operator_time >= start_timestamp) &
            (EssenceMessage.operator_time <= end_timestamp)
        )
        return query
    
    def _process_year_param(self, query, year_param: str):
        """处理年份参数。"""
        year = int(year_param)
        # 计算年份的开始和结束时间戳
        start_timestamp = int(datetime.datetime(year, 1, 1).timestamp())
        end_timestamp = int(datetime.datetime(year, 12, 31, 23, 59, 59).timestamp())
        # 按年查询
        query = query.where(
            (EssenceMessage.operator_time >= start_timestamp) &
            (EssenceMessage.operator_time <= end_timestamp)
        )
        return query
    
    def _process_limit_param(self, limit_param: str, default_limit: int):
        """处理限制条数参数。"""
        if limit_param == "-1":
            # -1表示返回所有
            return None
        elif limit_param.isdigit() and 1 <= int(limit_param) <= 100:
            # 1-100的数字
            return int(limit_param)
        return default_limit
    
    def _prepare_forward_messages(self, messages: list):
        """准备转发消息格式。"""
        forward_msgs = []
        for msg in messages:
            decoded_content = ast.literal_eval(msg.content)
            forward_msgs.append({
                "type": "node",
                "data": {
                    "name": msg.sender_nick,
                    "uin": msg.sender_id,
                    "content": decoded_content,
                    "time": msg.operator_time
                }
            })
        return forward_msgs