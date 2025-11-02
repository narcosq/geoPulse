"""Telegram Bot API client."""
from typing import Optional, Dict, Any
import aiohttp
from app.pkg.logger import logger
from app.pkg.settings.settings import get_settings

__all__ = ["TelegramClient"]


class TelegramClient:
    """Telegram Bot API client."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"{self.settings.TELEGRAM.BASE_URL}{self.settings.TELEGRAM.BOT_TOKEN}"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = "HTML",
        disable_notification: bool = False,
    ) -> Optional[str]:
        """Send message via Telegram Bot API.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (HTML/Markdown)
            disable_notification: Disable notification sound

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.settings.TELEGRAM.BOT_TOKEN:
            logger.warning("Telegram bot token not configured. Cannot send message.")
            return None

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        message_id = str(data.get("result", {}).get("message_id", ""))
                        logger.info(f"Successfully sent Telegram message: {message_id}")
                        return message_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Telegram message: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None

    async def send_location(
        self,
        chat_id: str,
        latitude: float,
        longitude: float,
        disable_notification: bool = False,
    ) -> Optional[str]:
        """Send location via Telegram Bot API.

        Args:
            chat_id: Telegram chat ID
            latitude: Latitude
            longitude: Longitude
            disable_notification: Disable notification sound

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.settings.TELEGRAM.BOT_TOKEN:
            logger.warning("Telegram bot token not configured. Cannot send location.")
            return None

        try:
            url = f"{self.base_url}/sendLocation"
            payload = {
                "chat_id": chat_id,
                "latitude": latitude,
                "longitude": longitude,
                "disable_notification": disable_notification,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        message_id = str(data.get("result", {}).get("message_id", ""))
                        logger.info(f"Successfully sent Telegram location: {message_id}")
                        return message_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Telegram location: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Failed to send Telegram location: {e}")
            return None

