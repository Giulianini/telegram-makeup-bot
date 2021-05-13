import logging
import os

from telegram import Update, File
from telegram.ext import CallbackContext

from bot.conversation.fsm import bot_states
from bot.conversation.makeup.utils import get_color_keyboard, get_image_from_bytearray, COLORS, image_to_bytearray
from bot.utils.bot_utils import BotUtils
from makeup.makeup import lips

logger = logging.getLogger(os.path.basename(__file__))


class LipsMakeup(object):
    # Constructor
    def __init__(self, config, auth_chat_ids, conversation_utils: BotUtils, face_aligner, face_segmenter):
        self.config = config
        self.auth_chat_ids = auth_chat_ids
        self.utils = conversation_utils
        # Makeup
        self.face_aligner = face_aligner
        self.face_segmenter = face_segmenter

    @staticmethod
    def show_lip_colors(update: Update, _context: CallbackContext):
        update.callback_query.answer()
        text = "Select a color"
        kb_markup = get_color_keyboard('lips')
        update.callback_query.edit_message_text(text=text, reply_markup=kb_markup)
        return bot_states.MAKEUP

    def lips_makeup_context(self, update: Update, _context: CallbackContext):
        makeup_config = self.auth_chat_ids[update.effective_chat.id]['makeup']
        update.callback_query.answer()
        color = update.callback_query.data
        color = color.split(':')[1]
        makeup_config['lip-color'] = color
        text = 'Send me a good photo\n\nIncrease effect with: "intensity 0.x"'
        update.callback_query.edit_message_text(text=text)
        return bot_states.LIPS

    def apply_makeup(self, update: Update, context: CallbackContext):
        makeup_config = self.auth_chat_ids[update.effective_chat.id]['makeup']
        if update.message.text:
            message_text = update.message.text
            saturate_value = message_text.split(' ')[1]
            makeup_config['lip-intensity'] = saturate_value
        if update.message.photo:
            file: File = context.bot.getFile(update.message.photo[-1].file_id)
            if file is not None:
                image_bytearray: bytes = file.download_as_bytearray()  # temporarily dump image to file and read as OpenCV frame
                image = get_image_from_bytearray(image_bytearray)

                image, landmarks = self.face_aligner.align(image)
                masks = self.face_segmenter.segment_image_keep_aspect_ratio(image)
                color = COLORS[makeup_config['lip-color']]
                hair_makeup_image = lips(image, masks, color, pronounced=True, force=0.2)

                temp_file = image_to_bytearray(hair_makeup_image)
                update.message.reply_photo(temp_file)
