import environ
import pdfminer.high_level
import re
from pdfminer.layout import LTTextContainer
from cv_checker.settings import MEDIA_ROOT, MEDIA_URL
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile, File
from bot.models import Vacancy, Candidate, Resume, Requirements
from typing import List, Tuple, cast

from telegram import (
    ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update
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

NAME, VACANCY, VACANCY_DESCRIPTION, COVER_LETTER, QUESTION1, QUESTION2, QUESTION3, QUESTION4, QUESTION5, EMAIL, FILE = range(11)

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
                VACANCY: [CallbackQueryHandler(self.list_button)],
                VACANCY_DESCRIPTION: [MessageHandler(Filters.text, self.vacancy_description)],
                COVER_LETTER: [MessageHandler(Filters.text, self.cover_letter)],
                QUESTION1 :  [CallbackQueryHandler(self.question1)],
                QUESTION2 :  [CallbackQueryHandler(self.question1)],
                QUESTION3 :  [CallbackQueryHandler(self.question1)],
                QUESTION4 :  [CallbackQueryHandler(self.question1)],
                QUESTION5 :  [MessageHandler(Filters.text, self.skills)],
                EMAIL :  [MessageHandler(Filters.text, self.email)],
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
            existing_resume = Resume.objects.get(candidate=existing_candidate)
            if existing_resume.file:
                update.message.reply_text('Resume for this name already existing')
                return ConversationHandler.END

        except Exception:
            logger.info(f"Candidate created with name {self.candidate.name}, surname {self.candidate.surname}")
            self.candidate.save()

        if not Vacancy.objects.filter(status=Vacancy.Status.Open).exists():
            update.message.reply_text('Sorry, no opened vacancies found')
            return ConversationHandler.END
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

        query.message.reply_text('Read the vacancy description:\n' + vacancy.description,
                                 reply_markup=ReplyKeyboardMarkup([['Confirm', 'Choose again']],
                                 one_time_keybord=True, input_field_placeholder='Confirm?'))
        return VACANCY_DESCRIPTION

    def vacancy_description(self, update: Update, context: CallbackContext):
        if update.message.text == 'Confirm':
            update.message.reply_text('Ok. Now write some short Cover Letter', reply_markup=ReplyKeyboardRemove())
            return COVER_LETTER
        else:
            update.message.reply_text('Please choose vacancy:', reply_markup=self.build_keyboard())
            return VACANCY

    def question1(self, update: Update, context: CallbackContext):
        # if update.message:
        query = update.callback_query
        query.answer()

        value = query.data

        try:
            existing_req = Requirements.objects.get(
                candidate=self.candidate, name=context.user_data['question']
            )
            requirements = existing_req
        except Exception:
            requirements = Requirements()
            requirements.candidate = self.candidate
            requirements.name = context.user_data['question']
            requirements.value = value
            requirements.save()
            logger.info(f'Requirements created for candidate {self.candidate}, {value}')
        
        if context.user_data.get('numb_question') == 1:
            context.user_data['question'] = 'Work experience'
            context.user_data['numb_question'] = 2
            query.message.reply_text('Please, choose your work experience.', reply_markup=self.question_experience())
            return QUESTION2
        elif context.user_data.get('numb_question') == 2:
            context.user_data['question'] = 'Type of employment'
            context.user_data['numb_question'] = 3
            query.message.reply_text('Please, choose type of employment you prefer.', reply_markup=self.question_time())
            return QUESTION3
        elif context.user_data.get('numb_question') == 3:
            context.user_data['question'] = 'Importance'
            context.user_data['numb_question'] = 4
            query.message.reply_text("What's most important to you?", reply_markup=self.question_important())
            return QUESTION4
        elif context.user_data.get('numb_question') == 4:
            context.user_data['question'] = 'Technical skills'
            context.user_data['numb_question'] = 5
            query.message.reply_text('Please, write your technical skills.', reply_markup=ReplyKeyboardRemove())
            return QUESTION5
        
        # else:
        #     update.message.reply_text('Please choose vacancy:', reply_markup=self.build_keyboard())
        #     return VACANCY

    def question_english(self) -> InlineKeyboardMarkup:
        english_levels = ["A1", "A2","B1", "B2"]

        button_list = [InlineKeyboardButton(
            level, callback_data=level)
            for level in english_levels]

        return InlineKeyboardMarkup.from_column(button_list)

    def question_time(self) -> InlineKeyboardMarkup:
        work_time = ["full-time", "part time"]

        button_list = [InlineKeyboardButton(
            level, callback_data=level)
            for level in work_time]

        return InlineKeyboardMarkup.from_column(button_list)

    def question_experience(self) -> InlineKeyboardMarkup:
        experience = ["0-1 year", "2-3 years", "3-6 years", "6+years"]

        button_list = [InlineKeyboardButton(
            level, callback_data=level)
            for level in experience]

        return InlineKeyboardMarkup.from_column(button_list)

    def question_important(self) -> InlineKeyboardMarkup:
        important = ["ability to work remotely", "ability to work from office", "ability to relocate from another city"]

        button_list = [InlineKeyboardButton(
            level, callback_data=level)
            for level in important]

        return InlineKeyboardMarkup.from_column(button_list)

    def cover_letter(self, update, context:CallbackContext):
        message_text = update.message.text

        self.resume.cover_letter = message_text
        self.resume.save()
        logger.info("Cover letter saved")

        context.user_data['numb_question'] = 1
        context.user_data['question'] = 'English'
        update.message.reply_text('Please, choose level of your English skills', reply_markup=self.question_english())
        return QUESTION1

    def skills(self, update, context:CallbackContext):
        message_text = update.message.text
        logger.info('skills')
        logger.info(message_text)
        logger.info(context.user_data['question'])
        try:
            existing_req = Requirements.objects.get(
                candidate=self.candidate, name=context.user_data['question']
            )
            logger.info(context.user_data['question'])
            requirements = existing_req
        except Exception:
            requirements = Requirements()
            requirements.candidate = self.candidate
            requirements.name = context.user_data['question']
            requirements.value = message_text
            requirements.save()
            logger.info(f'Requirements created for candidate {self.candidate},  {message_text}')

        logger.info("Skills saved")

        update.message.reply_text('Send your Resume as pdf file.')
        return FILE
    
    def email(self, update, context:CallbackContext):
        message_text = update.message.text
        logger.info('email')
        logger.info(message_text)
        
        email_regexp = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
        found_email = re.search(email_regexp, message_text)
        if found_email:
            self.candidate.email = found_email.group(0)
            self.candidate.save()
        else:
            update.message.reply_text('Wrong format. Try again.')
            return EMAIL

        logger.info("Email saved")

        update.message.reply_text('Thanks. Your Resume is saved. We will contact you after check')
        return ConversationHandler.END

    def file(self, update, context):
        new_file_name = f'{self.candidate.name}_{self.candidate.surname}.pdf'
        cv_path = f'{MEDIA_ROOT}/telegram/{new_file_name}'
        try:
            update.message.document.get_file().download(custom_path=cv_path)
            res = self.process_file(update, cv_path)
            f = open(cv_path, 'rb')
            self.resume.file.save(new_file_name, File(f))
            self.resume.save()
            logger.info(f'File downloaded to {self.resume.file.path}')
            self.resume.file.close()
            f.close()
        except Exception as e:
            logger.error(e)
            return self.handle_error(update, context)

        if res:
            return ConversationHandler.END
        else:
            return EMAIL

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

    def process_file(self, update, file_path):
        full_text = ''
        for page_layout in pdfminer.high_level.extract_pages(file_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    full_text += element.get_text()

        self.resume.extracted_text = full_text
        email_regexp = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
        found_email = re.search(email_regexp, full_text)
        self.resume.save()
        if found_email:
            self.candidate.email = found_email.group(0)
            self.candidate.save()
            update.message.reply_text('Thanks. Your Resume is saved. We will contact you after check')
            return True
        else:
            update.message.reply_text('We cant find your email in resume. Please, write your email here or send /cancel to end a conversation.')
            return False
        