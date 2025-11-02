"""Firebase Cloud Messaging client for push notifications."""
import json
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, messaging
from app.pkg.logger import logger
from app.pkg.settings.settings import get_settings

__all__ = ["FirebaseClient"]


class FirebaseClient:
    """Firebase Cloud Messaging client."""

    def __init__(self):
        self.settings = get_settings()
        self._initialized = False
        self._initialize()

    def _initialize(self):
        """Initialize Firebase Admin SDK."""
        if self._initialized:
            return

        try:
            if self.settings.FIREBASE.CREDENTIALS_PATH:
                cred = credentials.Certificate(self.settings.FIREBASE.CREDENTIALS_PATH)
            elif self.settings.FIREBASE.CREDENTIALS:
                cred_dict = json.loads(self.settings.FIREBASE.CREDENTIALS)
                cred = credentials.Certificate(cred_dict)
            else:
                logger.warning("Firebase credentials not provided. Push notifications will be disabled.")
                return

            firebase_admin.initialize_app(cred)
            self._initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self._initialized = False

    async def send_push_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: bool = True,
        priority: str = "high",
    ) -> Optional[str]:
        """Send push notification via FCM.

        Args:
            token: FCM token
            title: Notification title
            body: Notification body
            data: Additional data payload
            sound: Enable sound
            priority: Notification priority (high/normal)

        Returns:
            Message ID if successful, None otherwise
        """
        if not self._initialized:
            logger.warning("Firebase not initialized. Cannot send push notification.")
            return None

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                android=messaging.AndroidConfig(
                    priority="high" if priority == "high" else "normal",
                    notification=messaging.AndroidNotification(
                        sound="default" if sound else None,
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default.caf" if sound else None,
                            badge=1,
                        ),
                    ),
                ),
                data=data or {},
                token=token,
            )

            response = messaging.send(message)
            logger.info(f"Successfully sent FCM message: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to send FCM message: {e}")
            return None

