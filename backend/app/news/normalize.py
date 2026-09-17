import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "spm", "from", "ref"}


@dataclass(frozen=True)
class NormalizedArticle:
    source_guid: str | None
    canonical_url: str
    title: str
    normalized_title: str
    published_at: datetime | None
    feed_summary: str | None
    content_hash: str | None


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("article URL must be HTTP(S) with a host")
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in TRACKING_KEYS and not key.lower().startswith("utm_")
        )
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def normalize_title(value: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", clean_text(value).casefold())


def parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        date = datetime.fromisoformat(value)
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
    if date.tzinfo is None:
        return None
    return date.astimezone(UTC)


def normalize_entry(entry: dict[str, str]) -> NormalizedArticle:
    title = clean_text(entry.get("title", ""))
    if not title:
        raise ValueError("article title is empty")
    url = canonical_url(entry.get("link", ""))
    summary = clean_text(entry.get("summary", "")) or None
    # A feed summary is not the normalized article body and cannot identify duplicate content.
    content_hash = None
    return NormalizedArticle(
        source_guid=entry.get("id") or None,
        canonical_url=url,
        title=title,
        normalized_title=normalize_title(title),
        published_at=parse_published(entry.get("published")),
        feed_summary=summary,
        content_hash=content_hash,
    )
