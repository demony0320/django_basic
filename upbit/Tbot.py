import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor
class Tbot:
    def __init__(self,api_token,target_id):
        self.API_TOKEN = api_token
        self.TARGET_IDS = target_id 
        logging.basicConfig(level=logging.INFO)
        self.log = logging.getLogger('broadcast')
        self.bot = Bot(token=self.API_TOKEN, parse_mode=types.ParseMode.HTML)
        self.dp = Dispatcher(self.bot)
        
    async def send_message(self,user_id: int, text: str, disable_notification: bool = False) -> bool:
        """
        Safe messages sender
        :param user_id:
        :param text:
        :param disable_notification:
        :return:
        """
        try:
            await self.bot.send_message(user_id, text, disable_notification=disable_notification)
        except exceptions.BotBlocked:
            self.log.error(f"Target [ID:{user_id}]: blocked by user")
        except exceptions.ChatNotFound:
            self.log.error(f"Target [ID:{user_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            self.log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await send_message(user_id, text)  # Recursive call
        except exceptions.UserDeactivated:
            self.log.error(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            self.log.exception(f"Target [ID:{user_id}]: failed")
        else:
            self.log.info(f"Target [ID:{user_id}]: success")
            return True
        return False
    def broadcast(self,text: str):
        # Execute broadcaster
        for user_id in self.TARGET_IDS:
            executor.start(self.dp, self.send_message(user_id, text))

def main():
    #tbot = Tbot('2043458482:AAGRvooNJ4B7m4XHke-fhBgmgqUvz-sU1Ko',[-341574804])
    tbot = Tbot('2043458482:AAGRvooNJ4B7m4XHke-fhBgmgqUvz-sU1Ko',[-572675785])
    tbot.broadcast('mynameisjeff')

if __name__ == "__main__":
    main()
