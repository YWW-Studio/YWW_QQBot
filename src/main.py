# -*- coding: utf-8 -*-
"""Main module for YWW_QQBot.

This module initializes the NapCat client and sets up the command dispatcher.
"""

import asyncio
from napcat import NapCatClient, GroupMessageEvent, PrivateMessageEvent
from command_dispatch.command_dispatcher import CommandDispatcher
from command_dispatch.command_ctx import CommandContext

client = NapCatClient(
    ws_url="ws://127.0.0.1:3000",
    token="your_token"
)


async def main():
    """Main function to run the bot.
    
    Initializes the client, sets up the command context and dispatcher,
    and handles incoming events.
    """
    async with client:
        print(f"Bot {client.self_id} is connected")

        user_info = await client.get_login_info() 

        command_ctx = CommandContext()
        command_ctx.initialize(user_info, client)
        
        command_dispatcher = CommandDispatcher()
        
        async for event in client:
            if isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
                await command_dispatcher._try_handle_command_msg(event)

        command_ctx.cleanup()


if __name__ == "__main__":
    asyncio.run(main())