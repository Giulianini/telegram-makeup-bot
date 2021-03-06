import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Message
from telegram import Update

from bot.conversation.fsm import bot_states, bot_events
from bot.utils.bot_utils import BotUtils

logger = logging.getLogger(os.path.basename(__file__))


class RootCommand(object):
    # Constructor
    def __init__(self, config, auth_chat_ids, conversation_utils: BotUtils):
        self.config = config
        self.auth_chat_ids = auth_chat_ids
        self.utils = conversation_utils

    # STATE=START
    @staticmethod
    def start(update: Update, context):
        chat_id = update.effective_chat.id
        # Store value
        text = "Welcome to *Makeup Bot* by *NiNi* [link](https://github.com/Giulianini/makeup-bot)\n" \
               "Please insert bot password"
        context.bot.send_message(chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return bot_states.CREDENTIALS

    def credentials(self, update: Update, context):
        message: Message = update.message
        chat = message.chat
        text = message.text
        user = message.from_user
        chat_type = chat.type
        logger.info(chat_type)
        if text != self.config['credentials']:
            text = "🚫 User not allowed 🚫\nPlease insert bot password again"
            message = message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN_V2)
            self.utils.check_last_and_delete(update, context, message)
            log_msg = "{} ({} {}) denied.".format(user.username, user.first_name, user.last_name)
            if chat_type == 'group' or chat_type == 'supergroup':
                log_msg = "Group {} from {} ({} {}) denied.".format(chat.title, user.username, user.first_name,
                                                                    user.last_name)
            logger.warning(log_msg)
            self.utils.log_admin(log_msg, update, context)
            return bot_states.CREDENTIALS
        # Init user if not exists
        self.utils.init_user(chat.id, chat.username)
        log_msg = "{} ({} {}) active.".format(user.username, user.first_name, user.last_name)
        if chat_type == 'group' or chat_type == 'supergroup':
            log_msg = "Group {} from {} ({} {}) active.".format(chat.title, user.username, user.first_name,
                                                                user.last_name)
        logger.warning(log_msg)
        self.utils.log_admin(log_msg, update, context)
        text = "Login succeeded"
        message_out = message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN_V2)
        self.utils.delete_user_message(message)
        self.utils.check_last_and_delete(update, context, message_out)
        return bot_states.LOGGED

    def show_logged_menu(self, update: Update, context):
        self.utils.check_last_and_delete(update, context, None)
        keyboard = [[InlineKeyboardButton(text="Hair makeup", callback_data=str(bot_events.CHANGE_HAIR))],
                    [InlineKeyboardButton(text="Lips makeup", callback_data=str(bot_events.CHANGE_LIPS))],
                    [InlineKeyboardButton(text="❌", callback_data=str(bot_events.EXIT_CLICK))]
                    ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Check if callback or message
        if update.message:
            update.message.reply_text(text="Menu", reply_markup=reply_markup)
            self.utils.delete_user_message(update.message)
        elif update.callback_query:
            update.callback_query.edit_message_text(text="Menu", reply_markup=reply_markup)
        return bot_states.LOGGED

    @staticmethod
    def exit(update: Update, _):
        update.callback_query.answer()
        update.effective_message.delete()
        return bot_states.LOGGED
