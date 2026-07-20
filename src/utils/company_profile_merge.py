from __future__ import annotations

from src.domain.company_profile import CompanyProfile


def merge_company_profiles(primary: CompanyProfile, secondary: CompanyProfile) -> CompanyProfile:
    """Merge two company profiles while preferring the most trustworthy source URL."""
    merged_data: dict[str, object] = {}
    primary_data = primary.model_dump()
    secondary_data = secondary.model_dump()

    for field_name in primary_data:
        primary_value = primary_data[field_name]
        secondary_value = secondary_data[field_name]
        merged_value = _merge_field(field_name, primary_value, secondary_value)
        merged_data[field_name] = merged_value

    return CompanyProfile.model_validate(merged_data)


def _merge_field(field_name: str, primary_value: object, secondary_value: object) -> object:
    """Merge a single field according to the profile merge rules."""
    if field_name in {"products", "services", "erp_systems", "technologies", "source_urls"}:
        return _merge_unique_lists(primary_value, secondary_value)

    if field_name in {"website", "linkedin_url", "careers_url", "investor_relations_url", "news_url", "contact_url"}:
        return _merge_url_field(primary_value, secondary_value)

    if field_name in {"name", "description", "industry", "headquarters", "country", "revenue"}:
        if _has_meaningful_value(primary_value):
            return primary_value
        return secondary_value

    if field_name in {"employee_count", "founded_year"}:
        if primary_value is not None and not _is_placeholder_value(primary_value):
            return primary_value
        return secondary_value

    if primary_value is not None and not _is_placeholder_value(primary_value):
        return primary_value
    return secondary_value


def _merge_url_field(primary_value: object, secondary_value: object) -> object:
    """Prefer the highest-ranked URL while leaving the more specific social links intact."""
    primary_rank = _rank_url_value(primary_value)
    secondary_rank = _rank_url_value(secondary_value)

    if primary_rank is None and secondary_rank is None:
        return None
    if primary_rank is None:
        return secondary_value
    if secondary_rank is None:
        return primary_value
    if primary_rank < secondary_rank:
        return primary_value
    if secondary_rank < primary_rank:
        return secondary_value
    if _has_meaningful_value(primary_value):
        return primary_value
    return secondary_value


def _merge_unique_lists(primary_value: object, secondary_value: object) -> list[str]:
    """Merge list-like values without duplicates."""
    values: list[str] = []
    for item in list(primary_value or []) + list(secondary_value or []):
        normalized_item = _normalize_list_item(item)
        if normalized_item:
            values.append(normalized_item)
    return list(dict.fromkeys(values))


def _normalize_list_item(item: object) -> str | None:
    """Normalize a list item into a string value when possible."""
    if item is None:
        return None
    if isinstance(item, str):
        cleaned = item.strip()
        return cleaned or None
    if hasattr(item, "__str__"):
        cleaned = str(item).strip()
        return cleaned or None
    return None


def _rank_url_value(value: object) -> int | None:
    """Return a numeric priority for a URL-like value."""
    if value is None:
        return None
    if not _has_meaningful_value(value):
        return None
    url = str(value).lower()
    if "linkedin.com" in url:
        return 1
    if "investor" in url or "ir" in url:
        return 2
    if "career" in url or "/jobs" in url:
        return 3
    if "contact" in url:
        return 4
    if "wikipedia" in url:
        return 5
    if "crunchbase" in url:
        return 6
    if "zoominfo" in url:
        return 7
    if "news" in url or "blog" in url:
        return 8
    return 0


def _has_meaningful_value(value: object) -> bool:
    """Return True when a value is not None, empty, or a placeholder like 'Unknown'."""
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized not in {"", "unknown", "n/a", "none"}
    return True


def _is_placeholder_value(value: object) -> bool:
    """Return True for values that should be treated as empty placeholders."""
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"", "unknown", "n/a", "none"}
    return False
