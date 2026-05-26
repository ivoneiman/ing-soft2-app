import logging
import os
from calendar import monthrange
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)


def app_timezone():
    timezone_name = os.getenv("APP_TIMEZONE", "America/Buenos_Aires")
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logger.warning("[Time] timezone invalida: %s. Usando hora local del servidor.", timezone_name)
        return None


def current_datetime():
    timezone = app_timezone()
    return datetime.now(timezone) if timezone else datetime.now()


def datetime_in_app_timezone(value):
    if not value:
        return None

    timezone = app_timezone()
    if not timezone:
        return value

    if value.tzinfo:
        return value.astimezone(timezone)
    return value.replace(tzinfo=timezone)


def valid_test_day(value):
    try:
        day = int(value)
    except (TypeError, ValueError):
        return None
    return day if 1 <= day <= 31 else None


def discount_datetime_from_test_day(test_day):
    real_datetime = current_datetime()
    valid_day = valid_test_day(test_day)
    if valid_day is None:
        return real_datetime

    last_day = monthrange(real_datetime.year, real_datetime.month)[1]
    effective_datetime = real_datetime.replace(day=min(valid_day, last_day))
    logger.info(
        "[Discount] test_mode=true real_day=%s effective_day=%s",
        real_datetime.day,
        effective_datetime.day,
    )
    return effective_datetime
