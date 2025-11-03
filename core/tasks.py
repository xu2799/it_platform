import time
from celery import shared_task
from .models import Lesson
import logging

logger = logging.getLogger(__name__)

# 【重要说明】:
# 在实际生产环境中, 视频转码需要用到 FFmpeg, 并上传到阿里云/S3。
# 这里我们用一个 time.sleep(10) 来“模拟”这个耗时 10 秒的转码过程。

@shared_task
def process_video_upload(lesson_id, file_path): # file_path 现在是真实路径了
    logger.info(f"--- [任务启动] 正在处理 Lesson ID: {lesson_id} 的视频 ---")
    logger.info(f"--- 真实文件路径: {file_path} ---") # <-- 修改日志

    try:
        time.sleep(10)
        lesson = Lesson.objects.get(pk=lesson_id)

        # 2. Celery 模拟转码, 并更新 HLS 链接
        lesson.video_m3u8_url = f"https://example.com/hls/{lesson_id}/playlist.m3u8"
        lesson.lesson_type = Lesson.LESSON_VIDEO
        lesson.save()

        logger.info(f"--- [任务完成] Lesson ID: {lesson_id} HLS转码成功! URL已更新。 ---")
        return "Video processing successful"

    except Lesson.DoesNotExist:
        logger.error(f"Lesson ID {lesson_id} 不存在, 任务失败。")
        return "Lesson not found"
    except Exception as e:
        logger.error(f"处理视频时发生未知错误: {e}")
        return "Processing failed"