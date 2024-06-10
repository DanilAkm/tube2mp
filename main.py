#!/usr/bin/env python3

import telebot
import ssl
import logging
import os
import time
from dotenv import load_dotenv
from pytube import YouTube
from telebot import types

logger = logging.getLogger(__name__)

def download_audio(url: str):
  ssl._create_default_https_context = ssl._create_unverified_context
  try:
    video = YouTube(url, use_oauth=True, allow_oauth_cache=True)
    stream = video.streams.filter(only_audio=True).first()
    path = f"./files/{video.title.replace('/', '')}.mp3"
    stream.download(filename=path)
    logger.info("The video is downloaded in MP3")
    return path
  except TypeError as typo:
    logger.error(typo)
    raise typo
  except Exception as error:
    logger.error(error)
    raise error

def add_user(id: int, username: str) -> None:
  with open('./users/list.csv', 'r+') as users_file:
    lines = [line.rstrip() for line in users_file]
    if str(id) not in lines:
      users_file.write(f'{id}, {username}\n')

def main():
  load_dotenv()
  TG_TOKEN = os.getenv('TG_TOKEN')
  ADMIN_ID = os.getenv('ADMIN_ID')
  DONATION_LINK = os.getenv('DONATION_LINK')
  logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

  bot = telebot.TeleBot(TG_TOKEN)
  logger.info('Bot initialized')

  kb = types.InlineKeyboardMarkup(row_width=1)
  btn_types = types.InlineKeyboardButton(text='Donate', url=DONATION_LINK)
  kb.add(btn_types)

  bot.set_my_commands(
    commands=[
      telebot.types.BotCommand('help', 'Справка по боту'),
      telebot.types.BotCommand('donate', 'Задонатить на хостинг'),
      telebot.types.BotCommand('id', 'Получить свой id и ник')
    ]
  )   

  @bot.message_handler(commands=['start'])
  def send_welcome(message):
    bot.reply_to(message, "Send me a youtube video link - I'll give an mp3 of it\n")
    add_user(message.from_user.id, message.from_user.username)
    logger.info(f'User {message.chat.id} {message.from_user.username} joined the bot or triggered /start action')
  
  @bot.message_handler(commands=['help'])
  def give_help(message):
    bot.reply_to(message, 'Send a YT link, I\'m still not able to convert age restricted videos and send big files (apx longer than 2h)')

  @bot.message_handler(commands=['donate'])
  def donate(message):
    bot.reply_to(message, DONATION_LINK)
    bot.send_message(ADMIN_ID, f'@{message.from_user.username} requested donation - check account')

  @bot.message_handler(commands=['id'])
  def donate(message):
    bot.reply_to(message, f'{message.from_user.id} {message.from_user.username}')

  @bot.message_handler(content_types=['text'])
  def send_mp3(message):
    logger.info(f'User {message.from_user.username} requested mp3 audio of {message.text}')
    bot.send_message(message.chat.id, 'Работаем...')
    time.sleep(1)
    path = ''
    try:
      path = download_audio(message.text)
      with open(path, 'rb') as outfile:
        bot.send_audio(message.chat.id, outfile, reply_markup=kb)
        logger.info(f'{path} successfully sent to user {message.from_user.username} {message.from_user.username}')

    except Exception as error:
      with open('./error.mp3', 'rb') as errmsg:
        if 'regex_search' in str(error):
          error = 'invalid link'
        bot.send_audio(message.chat.id, errmsg, caption=error)
      logger.error(error)

    finally:
      bot.delete_message(message.chat.id, message.message_id + 1)
      if len(path) > 2:
        os.remove(path)

  bot.infinity_polling()

if __name__ == '__main__':
  main()
