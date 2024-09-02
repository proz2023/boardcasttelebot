import logging
import time
import json
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telethon import errors
from telethon.sync import TelegramClient

# Configure logging to suppress debug messages
logging.basicConfig(level=logging.WARNING)  # Suppress debug and info logs
logger = logging.getLogger("telethon")
logger.setLevel(logging.WARNING)  # Set Telethon's logging to WARNING

TOKEN: Final = "7449515379:AAFQnodKcqCofSA1AP9aCIMXdsWtKxT7KqE"
BOT_USERNAME: Final = "@botanslokalbotbot"
user_message = 'pesan'
sts_set_message = False
sts_run = False

def load_config(file_path):
    try:
        with open(file_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        return []

def save_config(file_path, config_data):
    with open(file_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_set_message
    sts_set_message = False
    await update.message.reply_text("Hallo coy !! ANSBOT.")

async def list_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_set_message
    sts_set_message = False
    config_data = load_config('config.json')
    
    if not config_data:
        await update.message.reply_text("You don't have an account.")
        return
    
    idx = 0
    for account in config_data:
        api_id = account["api_id"]
        api_hash = account["api_hash"]
        phone_number = account["phone_number"]
        session_name = account["session_name"]

        client = TelegramClient(session_name, api_id, api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            # Handle code request here
            # code = input('Enter the code: ')
            # await client.sign_in(phone_number, code)
        
        me = await client.get_me()
        await update.message.reply_text(f'{idx+1}. {me.username}')
        
        dialogs = await client.get_dialogs()
        response = "Groups:\n"
        
        for dialog in dialogs:
            if dialog.is_group:
                response += f"- {dialog.title}\n"

        await update.message.reply_text(response)
        await client.disconnect()

async def add_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello!')

async def set_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_set_message
    sts_set_message = True
    await update.message.reply_text("Masukkan Pesan Spam")

async def save_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_set_message
    if sts_set_message:
        global user_message
        user_message = update.message.text
        sts_set_message = False
        await update.message.reply_text("Spam Sudah updated")

async def view_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_set_message
    sts_set_message = False
    await update.message.reply_text(user_message)

async def send_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_run
    sts_run = True
    config_data = load_config('config.json')
    
    while sts_run:
        global sts_set_message
        sts_set_message = False
        
        for account in config_data:
            api_id = account["api_id"]
            api_hash = account["api_hash"]
            phone_number = account["phone_number"]
            session_name = account["session_name"]

            client = TelegramClient(session_name, api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                # Handle code request here
                # code = input('Enter the code: ')
                # await client.sign_in(phone_number, code)
            
            try:
                me = await client.get_me()
                dialogs = await client.get_dialogs()
                
                for dialog in dialogs:
                    if dialog.is_group:
                        retry_count = 0
                        while retry_count < 2:
                            try:
                                print(f"Sending a message to {dialog.id}")
                                await client.send_message(dialog.id, f'{user_message}')
                                time.sleep(1)  # Pause between messages
                                break  # Exit retry loop if message is sent successfully
                            except errors.ChatWriteForbiddenError as e:
                                print(f"Cannot send message to {dialog.title}: {e}")
                                break  # Exit retry loop on this error
                            except errors.UserBannedInChannelError as e:
                                print(f"User {me.username} is banned in {dialog.title}: {e}")
                                break  # Exit retry loop on this error
                            except errors.SlowModeWaitError as e:
                                print(f"Slow mode is enabled in {dialog.title}. Need to wait for {e.seconds} seconds.")
                                await update.message.reply_text(f"Slow mode detected. Waiting for {e.seconds} seconds before sending the next message.")
                                break  # Exit retry loop and retry after waiting
                            except errors.FloodWaitError as e:
                                print(f"Flood wait triggered. Need to wait for {e.seconds} seconds.")
                                await update.message.reply_text(f"Flood wait detected. Waiting for {e.seconds} seconds before sending the next message.")
                                break  # Exit retry loop and retry after waiting
                            except errors.ChannelPrivateError as e:
                                print(f"Cannot access {dialog.title}: {e}")
                                break  # Exit retry loop on this error
                            except errors.AuthKeyUnregisteredError as e:
                                print(f"Auth key is unregistered for user {me.username}: {e}")
                                await client.disconnect()
                                break  # Exit retry loop for the current account
                            except errors.PeerFloodError as e:
                                print(f"Peer flood error encountered: {e}")
                                await update.message.reply_text("Telegram has restricted you from sending messages for a while. Please wait before trying again.")
                                await client.disconnect()
                                break  # Exit retry loop for the current account
                            except errors.RPCError as e:
                                print(f"RPC error occurred: {e}")
                                retry_count += 1
                                if retry_count >= 2:
                                    print(f"Max retries reached for {dialog.title}. Skipping...")
                                    await update.message.reply_text(f"Failed to send message to {dialog.title} after multiple attempts.")
                                    break  # Exit retry loop and proceed to the next dialog
                                else:
                                    print(f"Retrying ({retry_count}/2)...")
                                    time.sleep(5)  # Wait before retrying
                            except Exception as e:
                                print(f"An unexpected error occurred: {e}")
                                break  # Exit retry loop for unexpected errors
                
                await update.message.reply_text(f"Account: {me.username} Sukses SPAM , Abis ini mulai lagi")
            finally:
                await client.disconnect()
        
        print("5 Menit akan dimulai spam lagi.")
        time.sleep(600)  # Wait for an hour before the next iteration

async def stop_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sts_run
    sts_run = True
    await update.message.reply_text("Spam Stopped")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

# Path to the configuration file
config_file_path = 'config.json'
# Load existing configuration
config_data = load_config(config_file_path)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('list', list_account_command))
    app.add_handler(CommandHandler('send', send_message_command))
    app.add_handler(CommandHandler('stop', stop_message_command))  # Re-added stop command
    app.add_handler(CommandHandler('set', set_message_command))
    app.add_handler(CommandHandler('view', view_message_command))

    app.add_handler(MessageHandler(filters.TEXT, save_message_command))

    app.run_polling(poll_interval=3)
