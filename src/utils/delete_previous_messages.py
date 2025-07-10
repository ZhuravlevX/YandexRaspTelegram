from aiogram.fsm.context import FSMContext


async def delete_previous_messages(messages: list, bot, last_message_id: int, state: FSMContext):
    for message_id in messages:
        if message_id['message_id'] == last_message_id:
            continue
        try:
            await bot.delete_message(chat_id=message_id['chat_id'], message_id=message_id['message_id'])
        except Exception as e:
            print(f"Failed to delete message {message_id['message_id']}: {e}")
    await state.update_data(messages=[])
