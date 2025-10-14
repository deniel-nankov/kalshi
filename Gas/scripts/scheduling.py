"""
Shared scheduling utilities for data source update times.

This module provides the DataSourceSchedule class which encapsulates
the update schedules for different data sources (EIA, RBOB, Retail prices).
"""

from datetime import datetime, timedelta


class DataSourceSchedule:
    """Data source update schedules"""
    
    # EIA updates: Wednesday 10:30 AM ET
    EIA_UPDATE_DAY = 2  # Wednesday (0 = Monday)
    EIA_UPDATE_HOUR = 15  # 10:30 AM ET = 15:30 UTC (approximate)
    EIA_UPDATE_MINUTE = 30
    
    # RBOB: Market hours Mon-Fri 9:30 AM - 4:00 PM ET
    RBOB_MARKET_OPEN_HOUR = 14  # 9:30 AM ET = ~14:30 UTC
    RBOB_MARKET_CLOSE_HOUR = 21  # 4:00 PM ET = ~21:00 UTC
    
    # Retail: Updates Monday morning with previous week data
    RETAIL_UPDATE_DAY = 0  # Monday
    RETAIL_UPDATE_HOUR = 12  # Noon ET = ~17:00 UTC
    
    @staticmethod
    def get_eia_update_time() -> datetime:
        """Get next EIA update time"""
        now = datetime.now()
        days_ahead = (DataSourceSchedule.EIA_UPDATE_DAY - now.weekday()) % 7
        if days_ahead == 0:
            # Today is Wednesday - check if update time has passed
            update_time = now.replace(
                hour=DataSourceSchedule.EIA_UPDATE_HOUR,
                minute=DataSourceSchedule.EIA_UPDATE_MINUTE,
                second=0,
                microsecond=0
            )
            if now >= update_time:
                days_ahead = 7  # Next week
        
        next_update = now + timedelta(days=days_ahead)
        next_update = next_update.replace(
            hour=DataSourceSchedule.EIA_UPDATE_HOUR,
            minute=DataSourceSchedule.EIA_UPDATE_MINUTE,
            second=0,
            microsecond=0
        )
        return next_update
    
    @staticmethod
    def is_market_hours() -> bool:
        """Check if it's currently market hours for RBOB"""
        now = datetime.now()
        # Market closed on weekends
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check market hours
        hour = now.hour
        return DataSourceSchedule.RBOB_MARKET_OPEN_HOUR <= hour <= DataSourceSchedule.RBOB_MARKET_CLOSE_HOUR
    
    @staticmethod
    def get_retail_update_time() -> datetime:
        """Get next retail price update time"""
        now = datetime.now()
        days_ahead = (DataSourceSchedule.RETAIL_UPDATE_DAY - now.weekday()) % 7
        if days_ahead == 0:
            # Today is Monday - check if update time has passed
            update_time = now.replace(
                hour=DataSourceSchedule.RETAIL_UPDATE_HOUR,
                minute=0,
                second=0,
                microsecond=0
            )
            if now >= update_time:
                days_ahead = 7  # Next week
        
        next_update = now + timedelta(days=days_ahead)
        next_update = next_update.replace(
            hour=DataSourceSchedule.RETAIL_UPDATE_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )
        return next_update
