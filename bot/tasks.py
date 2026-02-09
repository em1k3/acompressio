import os
import uuid
import asyncio
import subprocess
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientTimeout

FFMPEG_PATH = "ffmpeg/ffmpeg.exe"
FFPROBE_PATH = "ffmpeg/ffprobe.exe"
PROCESSED_DIR = "media/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

def compress_video_task(file_path: str, chat_id: int, bot_token: str, target_size_mb: int, compressing_msg_id: int):
    asyncio.run(_compress_and_send(file_path, chat_id, bot_token, target_size_mb, compressing_msg_id))


async def _compress_and_send(file_path: str, chat_id: int, bot_token: str, target_size_mb: int,
                             compressing_msg_id: int):
    """
    Асинхронная логика компрессии и отправки
    """
    bot = None
    try:
        duration = float(subprocess.check_output([
            FFPROBE_PATH,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ], text=True))

        target_bytes = target_size_mb * 1024 * 1024 * 0.9
        audio_bitrate = 128_000
        video_bitrate = int((target_bytes * 8 / duration) - audio_bitrate)

        video_bitrate = max(min(video_bitrate, 5_000_000), 100_000)

        output_name = f"compressed_{uuid.uuid4()}.mp4"
        output_path = os.path.join(PROCESSED_DIR, output_name)

        process1 = await asyncio.create_subprocess_exec(
            FFMPEG_PATH,
            "-y",
            "-i", file_path,
            "-c:v", "libx264",
            "-b:v", str(video_bitrate),
            "-pass", "1",
            "-an",
            "-f", "null",
            "NUL" if os.name == 'nt' else "/dev/null",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process1.communicate()

        process2 = await asyncio.create_subprocess_exec(
            FFMPEG_PATH,
            "-y",
            "-hwaccel", "cuda",
            "-i", file_path,
            "-c:v", "h264_nvenc",
            "-b:v", str(video_bitrate),
            "-preset", "veryfast",
            "-c:a", "aac",
            "-b:a", str(audio_bitrate),
            output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        if process2.returncode != 0:
            raise RuntimeError("ffmpeg failed")

        actual_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Target: {target_size_mb} MB, Actual: {actual_size_mb:.2f} MB")

        from aiogram.client.session.aiohttp import AiohttpSession
        from aiohttp import ClientTimeout

        timeout = ClientTimeout(total=300)
        session = AiohttpSession(timeout=timeout)

        bot = Bot(
            token=bot_token,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        try:
            await bot.delete_message(chat_id=chat_id, message_id=compressing_msg_id)
        except:
            pass

        # Отправляем результат
        video_file = FSInputFile(path=output_path)
        await bot.send_video(
            chat_id,
            video_file,
            caption=f"✅ Compressed: {actual_size_mb:.2f} MB (target: {target_size_mb} MB)",
            request_timeout=300
        )

        # Удаляем временные файлы ffmpeg
        try:
            os.remove("ffmpeg2pass-0.log")
            os.remove("ffmpeg2pass-0.log.mbtree")
        except:
            pass

        # Удаляем файлы
        os.remove(file_path)
        os.remove(output_path)

    except Exception as e:
        print(f"Error in compression task: {e}")
        if bot is None:
            bot = Bot(token=bot_token)
        try:
            await bot.send_message(chat_id, f"❌ Compression failed: {e}")
        except:
            pass
    finally:
        if bot:
            await bot.session.close()
