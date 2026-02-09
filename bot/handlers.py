from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from rq.job import Job
import os
import uuid

from bot.rq_queue import video_queue
from bot.tasks import compress_video_task

router = Router()

INCOMING_DIR = "media/incoming"
os.makedirs(INCOMING_DIR, exist_ok=True)

COMPRESSION_SIZES = [8, 20, 50, 100]

video_mappings = {}


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Welcome! Send a video file to compress.")


@router.message(F.video)
async def video_handler(message: Message):
    video = message.video
    file_id = video.file_id
    file_size_mb = video.file_size / (1024 * 1024)

    downloading_msg = await message.answer("Downloading your video...")

    await downloading_msg.delete()

    await message.answer(f"✅ Video downloaded! Size: {file_size_mb:.2f} MB")

    short_id = str(uuid.uuid4())[:8]
    video_mappings[short_id] = file_id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{size} MB",
            callback_data=f"c:{short_id}:{size}"
        )]
        for size in COMPRESSION_SIZES
    ])
    await message.answer("Choose output file size:", reply_markup=kb)


MAX_JOBS_PER_USER = 1
user_jobs = {}


@router.callback_query(lambda c: c.data and c.data.startswith("c:"))
async def handle_size_choice(callback: CallbackQuery):
    parts = callback.data.split(":")
    short_id = parts[1]
    target_size_mb = int(parts[2])
    user_id = callback.from_user.id

    if user_id in user_jobs:
        active_jobs = [j for j in user_jobs[user_id] if
                       Job.fetch(j, connection=video_queue.connection).get_status() in ['queued', 'started']]
        if len(active_jobs) >= MAX_JOBS_PER_USER:
            await callback.answer("⚠️ You already have a video being processed. Please wait!", show_alert=True)
            return
        user_jobs[user_id] = active_jobs

    source_path = video_mappings.get(short_id)
    if not source_path:
        await callback.answer("❌ Video not found. Please send again.")
        return

    bot_token = callback.bot.token

    compressing_msg = await callback.message.answer(f"🔄 Compressing to {target_size_mb} MB...")

    video_queue.enqueue(
        compress_video_task,
        source_path,
        callback.message.chat.id,
        bot_token,
        target_size_mb,
        compressing_msg.message_id
    )

    await callback.answer()
    await callback.message.delete()