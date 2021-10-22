import environ
from django.core.management.base import BaseCommand
from bot.models import Vacancy
from typing import List, Tuple, cast

from telegram import (
    ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext,
    InvalidCallbackData,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Setting Environment Variables
env = environ.Env()
environ.Env.read_env()

import logging

CV_CHECKER_BOT_KEY = env.str('CV_CHECKER_BOT_KEY')

NAME, VACANCY, COVER_LETTER, FILE = range(4)

class Command(BaseCommand):

    def handle(self, *args, **options):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

        updater = Updater(token=CV_CHECKER_BOT_KEY)
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                NAME: [MessageHandler(Filters.regex('^(.+) (.+)$'), self.name)],
                VACANCY: [MessageHandler(Filters.text, self.vacancy),
                          CallbackQueryHandler(self.list_button)],
                COVER_LETTER: [MessageHandler(Filters.text, self.cover_letter)],
                FILE: [MessageHandler(Filters.document, self.file)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

        # start_handler = CommandHandler('start', self.start)
        # dispatcher.add_handler(start_handler)
        dispatcher.add_handler(conv_handler)

        # updater.dispatcher.add_handler(CallbackQueryHandler(self.list_button))
        updater.dispatcher.add_handler(
            CallbackQueryHandler(self.handle_invalid_button, pattern=InvalidCallbackData)
        )

        updater.start_polling()
        updater.idle()


    def start(self, update, context):
        update.message.reply_text('Enter your name and surname')
        return NAME
        # update.message.reply_text('Please choose vacancy:', reply_markup=self.build_keyboard())

    def name(self, update, context):
        update.message.reply_text('Please choose vacancy:', reply_markup=self.build_keyboard())
        return VACANCY

    def build_keyboard(self) -> InlineKeyboardMarkup:
        opened_vacancies = Vacancy.objects.filter(status=Vacancy.Status.Open)

        button_list = [InlineKeyboardButton(
            it_vacancy.name, callback_data=it_vacancy.id)
            for it_vacancy in opened_vacancies]

        return InlineKeyboardMarkup.from_column(button_list)

    def list_button(self, update: Update, context: CallbackContext):
        """Parses the CallbackQuery and answers."""
        query = update.callback_query
        query.answer()

        vacancy_id = query.data

        query.message.reply_text('Ok. Now write some short Cover Letter')
        return COVER_LETTER

    def vacancy(self, update, context):
        update.message.reply_text('Ok. Now write some short Cover Letter')
        return COVER_LETTER

    def cover_letter(self, update, context):
        update.message.reply_text('Send your Resume as pdf file')
        return FILE

    def file(self, update, context):
        resume = update.message.document.get_file()
        resume.download()
        update.message.reply_text('Thanks. Your Resume is saved')
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext) -> int:
        """Cancels and ends the conversation."""
        update.message.reply_text(
            'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END

    def handle_invalid_button(self, update: Update, context: CallbackContext) -> None:
        """Informs the user that the button is no longer available."""
        update.callback_query.answer()
        update.effective_message.edit_text(
            'Sorry, I could not process this button click 😕 Please send /start to get a new keyboard.'
        )
