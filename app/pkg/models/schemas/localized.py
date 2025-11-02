"""Localized response schemas."""

from typing import Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field

from app.pkg.localization import Language, get_translator


class LocalizedResponse(PydanticBaseModel):
    """Base localized response with translated field descriptions."""

    @classmethod
    def localized_schema(cls, language: Language = Language.RU) -> Dict[str, Any]:
        """Get schema with localized field descriptions."""
        translator = get_translator()
        schema = cls.model_json_schema()

        def translate_schema(obj: Dict[str, Any], path: str = ""):
            """Recursively translate schema descriptions."""
            if isinstance(obj, dict):
                if "description" in obj and isinstance(obj["description"], str):
                    # Try to find translation key
                    desc_key = obj["description"]
                    if "." in desc_key:  # Looks like a translation key
                        obj["description"] = translator.t(desc_key, language)

                if "properties" in obj:
                    for prop_name, prop_data in obj["properties"].items():
                        new_path = f"{path}.{prop_name}" if path else prop_name
                        translate_schema(prop_data, new_path)

                if "items" in obj:
                    translate_schema(obj["items"], path)

        translate_schema(schema)
        return schema


def localized_field(translation_key: str, **kwargs) -> Field:
    """Create a pydantic Field with translation key as description."""
    return Field(description=translation_key, **kwargs)
