"""WITA timezone handling utilities.

Provides conversion between UTC and WITA (Asia/Makassar, UTC+8) timezones.
"""
from datetime import date
from datetime import datetime
from datetime import time
from zoneinfo import ZoneInfo


def get_wita_timezone() -> ZoneInfo:
    """Get WITA timezone object.

    Returns:
        ZoneInfo for WITA timezone (Asia/Makassar, UTC+8)
    """
    from src.config.settings import get_settings

    settings = get_settings()
    return ZoneInfo(settings.timezone)


def utc_to_wita(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to WITA timezone.

    Args:
        utc_dt: UTC datetime (timezone-aware or naive)

    Returns:
        WITA datetime (timezone-aware)

    Examples:
        >>> from datetime import datetime
        >>> utc_dt = datetime(2025, 12, 18, 16, 0, 0)  # 16:00 UTC
        >>> wita_dt = utc_to_wita(utc_dt)
        >>> wita_dt.hour
        0  # 00:00 WITA (next day)
    """
    # Ensure UTC timezone
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    elif utc_dt.tzinfo != ZoneInfo("UTC"):
        utc_dt = utc_dt.astimezone(ZoneInfo("UTC"))

    # Convert to WITA
    return utc_dt.astimezone(get_wita_timezone())


def wita_to_utc(wita_dt: datetime) -> datetime:
    """Convert WITA datetime to UTC timezone.

    Args:
        wita_dt: WITA datetime (timezone-aware or naive)

    Returns:
        UTC datetime (timezone-aware)

    Examples:
        >>> from datetime import datetime
        >>> wita_dt = datetime(2025, 12, 19, 0, 0, 0)  # 00:00 WITA
        >>> utc_dt = wita_to_utc(wita_dt)
        >>> utc_dt.hour
        16  # 16:00 UTC (previous day)
    """
    # Ensure WITA timezone
    if wita_dt.tzinfo is None:
        wita_dt = wita_dt.replace(tzinfo=get_wita_timezone())
    elif wita_dt.tzinfo != get_wita_timezone():
        wita_dt = wita_dt.astimezone(get_wita_timezone())

    # Convert to UTC
    return wita_dt.astimezone(ZoneInfo("UTC"))


def get_current_wita_datetime() -> datetime:
    """Get current datetime in WITA timezone.

    Returns:
        Current WITA datetime (timezone-aware)
    """
    return datetime.now(get_wita_timezone())


def get_current_wita_date() -> date:
    """Get current date in WITA timezone.

    Returns:
        Current WITA date

    Note:
        This is important for daily reports - a transaction at 23:30 UTC
        on Dec 18 is actually Dec 19 in WITA timezone.
    """
    return get_current_wita_datetime().date()


def get_wita_date_from_utc(utc_dt: datetime) -> date:
    """Extract WITA date from UTC datetime.

    Args:
        utc_dt: UTC datetime

    Returns:
        Date in WITA timezone

    Examples:
        >>> from datetime import datetime
        >>> utc_dt = datetime(2025, 12, 18, 16, 30, 0)  # 16:30 UTC
        >>> get_wita_date_from_utc(utc_dt)
        date(2025, 12, 19)  # Next day in WITA
    """
    wita_dt = utc_to_wita(utc_dt)
    return wita_dt.date()


def get_wita_start_of_day(wita_date: date) -> datetime:
    """Get start of day (00:00:00) in WITA for a given date.

    Args:
        wita_date: Date in WITA timezone

    Returns:
        WITA datetime at 00:00:00 of the given date
    """
    return datetime.combine(wita_date, time.min, tzinfo=get_wita_timezone())


def get_wita_end_of_day(wita_date: date) -> datetime:
    """Get end of day (23:59:59) in WITA for a given date.

    Args:
        wita_date: Date in WITA timezone

    Returns:
        WITA datetime at 23:59:59 of the given date
    """
    return datetime.combine(wita_date, time.max, tzinfo=get_wita_timezone())


def format_wita_datetime(dt: datetime) -> str:
    """Format datetime as WITA timezone string.

    Args:
        dt: Datetime (any timezone)

    Returns:
        Formatted string (e.g., "2025-12-18 08:30 WITA")
    """
    wita_dt = utc_to_wita(dt) if dt.tzinfo == ZoneInfo("UTC") else dt
    return wita_dt.strftime("%Y-%m-%d %H:%M WITA")
