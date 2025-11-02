"""Google Maps API client."""
from typing import Optional, Dict, Any
import googlemaps
from decimal import Decimal
from app.pkg.logger import logger
from app.pkg.settings.settings import get_settings

__all__ = ["GoogleMapsClient"]


class GoogleMapsClient:
    """Google Maps API client for geocoding and reverse geocoding."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        if self.settings.GOOGLE_MAPS.API_KEY:
            try:
                self.client = googlemaps.Client(key=self.settings.GOOGLE_MAPS.API_KEY)
                logger.info("Google Maps client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps client: {e}")

    async def reverse_geocode(
        self, latitude: Decimal, longitude: Decimal
    ) -> Optional[Dict[str, Any]]:
        """Reverse geocode coordinates to address.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Address information dictionary or None
        """
        if not self.client:
            logger.warning("Google Maps client not initialized. Cannot reverse geocode.")
            return None

        try:
            result = self.client.reverse_geocode((float(latitude), float(longitude)))
            if result and len(result) > 0:
                address_components = result[0].get("address_components", [])
                formatted_address = result[0].get("formatted_address", "")

                address_info = {
                    "formatted_address": formatted_address,
                    "components": {},
                }

                for component in address_components:
                    types = component.get("types", [])
                    if "street_number" in types:
                        address_info["components"]["street_number"] = component.get("long_name")
                    elif "route" in types:
                        address_info["components"]["route"] = component.get("long_name")
                    elif "locality" in types:
                        address_info["components"]["city"] = component.get("long_name")
                    elif "country" in types:
                        address_info["components"]["country"] = component.get("long_name")

                return address_info
            return None
        except Exception as e:
            logger.error(f"Failed to reverse geocode: {e}")
            return None

    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """Geocode address to coordinates.

        Args:
            address: Address string

        Returns:
            Coordinates dictionary with lat/lng or None
        """
        if not self.client:
            logger.warning("Google Maps client not initialized. Cannot geocode.")
            return None

        try:
            result = self.client.geocode(address)
            if result and len(result) > 0:
                location = result[0].get("geometry", {}).get("location", {})
                return {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to geocode: {e}")
            return None

