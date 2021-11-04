import environ
import pdfminer.high_level
from pdfminer.layout import LTTextContainer
from cv_checker.settings import MEDIA_ROOT, MEDIA_URL
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile, File
from bot.models import Vacancy, Candidate, Resume
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.INFO)

logger = logging.getLogger(__name__)

CV_CHECKER_BOT_KEY = env.str('CV_CHECKER_BOT_KEY')

NAME, VACANCY, COVER_LETTER, FILE = range(4)

class Command(BaseCommand):

    candidate = Candidate()
    resume = Resume()

    def handle(self, *args, **options):

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
        # reset class variables
        self.candidate = Candidate()
        self.resume = Resume()

        update.message.reply_text('Enter your name and surname')
        return NAME
        # update.message.reply_text('Please choose vacancy:', reply_markup=self.build_keyboard())

    def name(self, update, context):
        message_text = update.message.text
        message_parts = message_text.split(' ')
        if (len(message_parts) != 2):
            logger.warning(f'Wrong user name and surname: {message_text}')
            return self.handle_error(update, context)

        self.candidate.name = message_parts[0]
        self.candidate.surname = message_parts[1]

        try:
            existing_candidate = Candidate.objects.get(
                name=self.candidate.name, surname=self.candidate.surname
            )
            logger.info(f'candiadate already exists id = {existing_candidate.id}')
            self.candidate = existing_candidate
        except Exception:
            logger.info(f"Candidate created with name {self.candidate.name}, surname {self.candidate.surname}")
            self.candidate.save()

        update.message.reply_text('Please choose vacancy:', reply_markup=self.build_keyboard())
        return VACANCY

    def vacancy(self, update, context):
        update.message.reply_text('Ok. Now write some short Cover Letter')
        return COVER_LETTER

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
        try:
            vacancy = Vacancy.objects.get(id=vacancy_id)
        except Exception:
            return self.handle_error(update, context)

        try:
            existing_resume = Resume.objects.get(
                candidate=self.candidate, vacancy=vacancy
            )
            self.resume = existing_resume
        except Exception:
            self.resume.candidate = self.candidate
            self.resume.vacancy = vacancy
            self.resume.save()
            logger.info(f'Resume created for candidate {self.candidate}, vacancy {vacancy}')

        query.message.reply_text('Ok. Now write some short Cover Letter')
        return COVER_LETTER

    def cover_letter(self, update, context):
        message_text = update.message.text

        self.resume.cover_letter = message_text
        self.resume.save()
        logger.info("Cover letter saved")

        update.message.reply_text('Send your Resume as pdf file')
        return FILE

    def file(self, update, context):
        new_file_name = f'{self.candidate.name}_{self.candidate.surname}.pdf'
        cv_path = f'{MEDIA_ROOT}/telegram/{new_file_name}'
        try:
            update.message.document.get_file().download(custom_path=cv_path)
            self.process_file(cv_path)
            f = open(cv_path, 'rb')
            self.resume.file.save(new_file_name, File(f))
            self.resume.save()
            logger.info(f'File downloaded to {self.resume.file.path}')
            self.resume.file.close()
            f.close()
        except Exception:
            return self.handle_error(update, context)


        update.message.reply_text('Thanks. Your Resume is saved')
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext) -> int:
        """Cancels and ends the conversation."""
        update.message.reply_text(
            'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
        )

        logger.info("Cancelling conversation")

        return ConversationHandler.END

    def handle_invalid_button(self, update: Update, context: CallbackContext) -> None:
        """Informs the user that the button is no longer available."""
        update.callback_query.answer()
        update.effective_message.edit_text(
            'Sorry, I could not process this button click 😕 Please send /start to get a new keyboard.'
        )

    def handle_error(self, update, context):
        update.message.reply_text(
            'Sorry, something went wrong.', reply_markup=ReplyKeyboardRemove()
        )

        logger.info("Error ending conversation")

        return ConversationHandler.END

    def process_file(self, file_path):
        full_text = ''
        for page_layout in pdfminer.high_level.extract_pages(file_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    full_text += element.get_text()

        self.resume.extracted_text = full_text
        self.resume.save()