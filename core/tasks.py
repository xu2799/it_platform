import time
import os
from celery import shared_task
from .models import Lesson
import logging

logger = logging.getLogger(__name__)

# 【重要说明】:
# 在实际生产环境中, 视频转码需要用到 FFmpeg, 并上传到阿里云/S3。
# 这里我们用一个 time.sleep(10) 来"模拟"这个耗时 10 秒的转码过程。

@shared_task(bind=True, max_retries=3)
def process_video_upload(self, lesson_id, file_path):
    """
    处理视频上传任务
    :param lesson_id: 课时ID
    :param file_path: 视频文件路径
    :return: 处理结果
    """
    logger.info(f"--- [任务启动] 正在处理 Lesson ID: {lesson_id} 的视频 ---")
    logger.info(f"--- 文件路径: {file_path} ---")

    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"视频文件不存在: {file_path}")
        
        # 模拟视频处理（实际应该使用FFmpeg进行转码）
        logger.info(f"开始处理视频，预计需要10秒...")
        time.sleep(10)
        
        # 获取课时对象
        lesson = Lesson.objects.get(pk=lesson_id)
        
        # 更新课时状态
        # 在实际生产环境中，这里应该：
        # 1. 使用FFmpeg将MP4转换为HLS格式
        # 2. 上传到云存储（如阿里云OSS、AWS S3等）
        # 3. 获取HLS播放列表URL
        
        # 保存相对路径到 video_m3u8_url，前端会自动补全 API_URL
        # 格式: /media/lesson_videos_mp4/xxx.mp4
        if lesson.video_mp4_file:
            # 获取文件的相对路径（相对于 MEDIA_ROOT）
            file_path = lesson.video_mp4_file.name
            # 确保路径以 /media/ 开头（前端需要这个格式）
            if not file_path.startswith('/'):
                from django.conf import settings
                lesson.video_m3u8_url = f"{settings.MEDIA_URL}{file_path}"
            else:
                lesson.video_m3u8_url = file_path
            logger.info(f"保存视频URL: {lesson.video_m3u8_url}")
        else:
            logger.error("lesson.video_mp4_file 为空，无法保存视频URL")
            
        lesson.lesson_type = Lesson.LESSON_VIDEO
        lesson.content = ""  # 清空"视频正在处理中..."的提示
        lesson.save()

        logger.info(f"--- [任务完成] Lesson ID: {lesson_id} 视频处理成功! URL已更新。 ---")
        return {"status": "success", "lesson_id": lesson_id, "message": "Video processing successful"}

    except Lesson.DoesNotExist:
        error_msg = f"Lesson ID {lesson_id} 不存在, 任务失败。"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    except FileNotFoundError as e:
        error_msg = f"文件不存在: {str(e)}"
        logger.error(error_msg)
        # 更新课时状态为错误
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
            lesson.content = f"视频处理失败: {error_msg}"
            lesson.save()
        except:
            pass
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"处理视频时发生未知错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 更新课时状态为错误
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
            lesson.content = f"视频处理失败，请重新上传。错误: {str(e)}"
            lesson.save()
        except:
            pass
        
        # 如果重试次数未达到上限，则重试
        if self.request.retries < self.max_retries:
            logger.info(f"任务失败，将在10秒后重试 (第 {self.request.retries + 1} 次)...")
            raise self.retry(countdown=10, exc=e)
        
        return {"status": "error", "message": error_msg}