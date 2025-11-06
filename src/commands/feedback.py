import os

from aiogram.fsm.state import StatesGroup, State

from aiogram import Bot, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from dotenv import load_dotenv

load_dotenv()

feedback = Router()
admin_id = os.getenv('ADMIN_ID')


class FeedbackStates(StatesGroup):
    awaiting_feedback = State()
    awaiting_reply_text = State()


@feedback.message(Command('feedback'))
@feedback.callback_query(lambda c: c.data == 'feedback')
async def feedback_command(event, state: FSMContext):
    user_state = await state.get_data()

    if user_state.get('feedback_in_progress'):
        if isinstance(event, Message):
            await event.answer(
                "ℹ✉ <b>У вас уже есть одно открытое обращение. Пожалуйста, дождитесь ответа. Если вам уже ответили на обращение, то отметьте его прочитанным, перед тем, как написать следующее.</b>",
            )
        elif isinstance(event, CallbackQuery):
            await event.message.answer(
                "ℹ✉ <b>У вас уже есть одно открытое обращение. Пожалуйста, дождитесь ответа. Если вам уже ответили на обращение, то отметьте его прочитанным, перед тем, как написать следующее.</b>",
            )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ | Отменить обращение", callback_data="cancel_feedback")]
        ])

    if isinstance(event, Message):
        feedback_message = await event.answer(
            "📨 <b>Пожалуйста, напишите ваше сообщение, которое будет передано создателю бота. \n\n</b>"
            "В своем сообщении вы можете рассказать об пожеланиях, обнаруженных ошибках и багах, оставить отзыв по поводу использования бота. "
            "Убедительная просьба, не писать в обратную связь всякий не связанный бред, имейте уважение.",
            reply_markup=keyboard)
    elif isinstance(event, CallbackQuery):
        feedback_message = await event.message.answer(
            "📨 <b>Пожалуйста, напишите ваше сообщение, которое будет передано создателю бота. \n\n</b>"
            "В своем сообщении вы можете рассказать об пожеланиях, обнаруженных ошибках и багах, оставить отзыв по поводу использования бота. "
            "Убедительная просьба, не писать в обратную связь всякий не связанный бред, имейте уважение.",
            reply_markup=keyboard)

    await state.update_data(feedback_message_id=feedback_message.message_id, feedback_chat_id=feedback_message.chat.id)
    await state.set_state(FeedbackStates.awaiting_feedback)

    try:
        await event.delete()
    except Exception:
        pass


@feedback.message(FeedbackStates.awaiting_feedback)
async def handle_feedback(message: Message, state: FSMContext, bot: Bot):
    feedback_text = message.text
    user = message.from_user
    state_data = await state.get_data()
    feedback_message_id = state_data.get('feedback_message_id')
    feedback_chat_id = state_data.get('feedback_chat_id')

    feedback_message = (
        f"💌 <b>У вас появилось новое обращение от {user.full_name} (@{user.username}):</b>\n\n{feedback_text}\n\n"
        f"<b>Для ответа пользователю используйте кнопку ниже.</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ | Ответить пользователю", callback_data=f"reply_{user.id}")]
        ]
    )

    await bot.send_message(chat_id=admin_id, text=feedback_message, reply_markup=keyboard)
    await bot.edit_message_text("📧 <b>Спасибо за обратную связь! В течении времени вам ответит создатель бота.</b>",
                                chat_id=feedback_chat_id,
                                message_id=feedback_message_id,
                                )
    await state.update_data(feedback_in_progress=True)
    await state.set_state()


@feedback.callback_query(lambda c: c.data.startswith("reply_"))
async def ask_reply_text(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.message.chat.id != int(admin_id):
        return
    user_id = int(callback_query.data.split("_")[1])
    reply_prompt_message = await bot.send_message(chat_id=admin_id,
                                                  text="📝 <b>Пожалуйста, введите текст ответа пользователю:</b>")
    await state.update_data(reply_user_id=user_id, reply_prompt_message_id=reply_prompt_message.message_id)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await state.set_state(FeedbackStates.awaiting_reply_text)


@feedback.callback_query(lambda c: c.data == 'cancel_feedback')
async def cancel_feedback_reply_text(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("❌📧 <b>Вы отменили обратную связь с создателем бота.</b>")
    await state.update_data(feedback_in_progress=False)
    await state.set_state()


@feedback.callback_query(lambda c: c.data == 'read_feedback')
async def read_feedback(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(feedback_in_progress=False)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await state.set_state()


@feedback.message(FeedbackStates.awaiting_reply_text)
async def send_reply(message: Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    user_id = state_data.get("reply_user_id")
    reply_text = message.text
    reply_prompt_message_id = state_data.get('reply_prompt_message_id')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ | Пометить прочитанным", callback_data="read_feedback")]
        ]
    )

    try:
        await bot.send_message(chat_id=user_id,
                               text=f"📩 <b>Вам поступило сообщение от создателя бота в ответ на ваше обращение:</b>\n\n{reply_text}",
                               reply_markup=keyboard)
        await bot.edit_message_text("📧 <b>Сообщение было успешно отправлено пользователю.</b>",
                                    chat_id=admin_id,
                                    message_id=reply_prompt_message_id)
    except Exception as e:
        await message.answer(f"❌ <b>Не удалось отправить сообщение пользователю. Ошибка:</b> {e}")
    await state.set_state()
