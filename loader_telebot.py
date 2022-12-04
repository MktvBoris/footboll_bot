from telebot import TeleBot

from config_data import config

bot: TeleBot = TeleBot(token=config.BOT_TOKEN)
