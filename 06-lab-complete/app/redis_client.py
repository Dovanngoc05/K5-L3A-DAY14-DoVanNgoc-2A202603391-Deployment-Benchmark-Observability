"""
Kết nối Redis dùng chung cho rate limiter và cost guard.

Yêu cầu:
  • Đọc REDIS_URL từ config
  • App vẫn phải KHỞI ĐỘNG ĐƯỢC khi Redis chưa sẵn sàng (đừng ping Redis lúc import)
  • redis_healthy() dùng cho GET /ready: Redis không kết nối được → False
"""
import redis
from redis.exceptions import RedisError

from app.config import settings

r = redis.Redis.from_url(settings.redis_url, decode_responses=True)  # TODO: tạo client, vd redis.from_url(settings.redis_url, decode_responses=True)


def redis_healthy() -> bool:
    try:
        return bool(r.ping())
    except RedisError:
        return False
