#!/usr/bin/env python3
"""Search reachable video platforms and rank candidates for AskWhy nodes."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import socket
import ssl
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


SCHEMA_VERSION = "1.0"
PLATFORMS = ("bilibili", "youtube")
PLATFORM_CONCURRENCY = {
    "bilibili": 1,
    "youtube": 2,
}
PLATFORM_MIN_INTERVAL = {
    "bilibili": 0.6,
    "youtube": 0.0,
}
PROBES = {
    "bilibili": "https://www.bilibili.com/",
    "youtube": "https://www.youtube.com/",
}
POSITIVE_TERMS = {
    "原理",
    "科普",
    "解释",
    "实验",
    "课堂",
    "讲解",
    "知识",
    "教程",
    "为什么",
    "如何",
    "科学",
    "物理",
    "机制",
    "证明",
    "推导",
    "测量",
    "动画",
    "explained",
    "explanation",
    "science",
    "physics",
    "experiment",
    "lecture",
    "lesson",
    "how",
    "why",
}
NEGATIVE_TERMS = {
    "不可思议",
    "震惊",
    "必看",
    "全网最",
    "秒杀",
    "猎奇",
    "毁三观",
    "鬼畜",
    "歌曲",
    "音乐",
    "mv",
    "塔罗",
    "占卜",
    "游戏",
    "速通",
    "攻略",
    "影视",
    "综艺",
    "电视剧",
    "动漫",
    "广告",
    "带货",
    "搞笑",
    "整活",
    "直播回放",
    "吃鸡",
    "王者荣耀",
    "我的世界",
    "混剪",
    "反应",
    "reaction",
    "shorts",
    "meme",
    "song",
    "music",
    "gameplay",
    "trailer",
}
SEVERE_NEGATIVE_TERMS = {
    "鬼畜",
    "歌曲",
    "音乐",
    "塔罗",
    "占卜",
    "游戏",
    "速通",
    "攻略",
    "电视剧",
    "带货",
    "直播回放",
    "reaction",
    "meme",
    "song",
    "gameplay",
}
STOP_TERMS = {
    "",
    "为什么",
    "是什么",
    "怎么",
    "怎样",
    "如何",
    "什么",
    "真的",
    "可以",
    "能够",
    "到底",
    "一个",
    "一种",
    "这个",
    "那个",
    "我们",
    "它们",
    "的",
    "了",
    "会",
    "吗",
    "呢",
    "和",
    "与",
    "是",
    "在",
}
TRUSTED_CHANNEL_TERMS = {
    "中国科学院",
    "中国科协",
    "科普中国",
    "国家天文台",
    "物理所",
    "李永乐",
    "妈咪说",
    "不刷题的吴姥姥",
    "Veritasium",
    "Kurzgesagt",
    "CrashCourse",
    "TED-Ed",
    "PBS",
    "BBC",
    "NASA",
    "MIT",
    "MinutePhysics",
    "SciShow",
    "OpenStax",
}
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
ASCII_TERM_RE = re.compile(r"[a-z0-9]+")
CJK_RUN_RE = re.compile(r"[\u3400-\u9fff]+")
_HTTP_LOCAL = threading.local()
_PLATFORM_PACING_LOCK = threading.Lock()
_PLATFORM_LAST_REQUEST: dict[str, float] = {}
_BILIBILI_HTTP_LOCK = threading.Lock()
_BILIBILI_HTTP_CLIENT = None


def _http_client():
    client = getattr(_HTTP_LOCAL, "client", None)
    if client is None:
        client = build_opener(HTTPCookieProcessor(CookieJar()))
        _HTTP_LOCAL.client = client
    return client


def _pace_platform(platform: str) -> None:
    interval = PLATFORM_MIN_INTERVAL.get(platform, 0.0)
    if interval <= 0:
        return
    with _PLATFORM_PACING_LOCK:
        now = time.monotonic()
        last = _PLATFORM_LAST_REQUEST.get(platform, 0.0)
        wait = interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        _PLATFORM_LAST_REQUEST[platform] = time.monotonic()


@dataclass
class SearchError(RuntimeError):
    platform: str
    message: str
    kind: str = "search"

    def as_dict(self) -> dict[str, str]:
        return {
            "platform": self.platform,
            "kind": self.kind,
            "message": self.message,
        }


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def clean_text(value: Any) -> str:
    text = html.unescape(TAG_RE.sub("", str(value or "")))
    return SPACE_RE.sub(" ", text).strip()


def normalized(value: str) -> str:
    return SPACE_RE.sub(" ", value.casefold()).strip()


def text_terms(value: str) -> set[str]:
    text = normalized(value)
    terms = {
        term
        for term in ASCII_TERM_RE.findall(text)
        if len(term) >= 2 and term not in STOP_TERMS
    }
    for run in CJK_RUN_RE.findall(text):
        if len(run) == 1:
            terms.add(run)
            continue
        for index in range(len(run) - 1):
            bigram = run[index : index + 2]
            if bigram not in STOP_TERMS:
                terms.add(bigram)
    return terms


def parse_duration(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{1,2})", text)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)


def parse_count(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return max(0, value)
    text = clean_text(value).casefold().replace(",", "").replace(" ", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*([万k亿m]?)", text)
    if not match:
        return None
    amount = float(match.group(1))
    multiplier = {
        "": 1,
        "k": 1_000,
        "万": 10_000,
        "m": 1_000_000,
        "亿": 100_000_000,
    }[match.group(2)]
    return round(amount * multiplier)


def _failure_kind(error: BaseException) -> str:
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, socket.gaierror):
        return "dns"
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(reason, ssl.SSLError):
        return "tls"
    if isinstance(reason, ConnectionError):
        return "connection"
    return "network"


def request_headers(url: str) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
    }
    if urlparse(url).hostname and "bilibili.com" in urlparse(url).hostname:
        headers["Referer"] = "https://www.bilibili.com/"
    return headers


def fetch_url(url: str, timeout: float, *, body: bool = False) -> tuple[int, bytes]:
    global _BILIBILI_HTTP_CLIENT
    headers = request_headers(url)
    if not body:
        headers["Range"] = "bytes=0-0"
    request = Request(url, headers=headers)
    if "bilibili.com" in (urlparse(url).hostname or ""):
        with _BILIBILI_HTTP_LOCK:
            if _BILIBILI_HTTP_CLIENT is None:
                _BILIBILI_HTTP_CLIENT = build_opener(
                    HTTPCookieProcessor(CookieJar())
                )
            with _BILIBILI_HTTP_CLIENT.open(request, timeout=timeout) as response:
                return (
                    int(getattr(response, "status", 0) or 0),
                    response.read() if body else b"",
                )
    with _http_client().open(request, timeout=timeout) as response:
        return int(getattr(response, "status", 0) or 0), response.read() if body else b""


def probe_url(url: str, timeout: float = 4.0) -> dict[str, Any]:
    started = time.monotonic()
    status: int | None = None
    failure_kind: str | None = None
    try:
        status, _ = fetch_url(url, timeout)
    except HTTPError as error:
        status = int(error.code)
        failure_kind = "http"
    except (OSError, URLError) as error:
        failure_kind = _failure_kind(error)
    latency_ms = round((time.monotonic() - started) * 1000)
    reachable = status is not None and 200 <= status < 400
    return {
        "reachable": reachable,
        "httpStatus": status,
        "latencyMs": latency_ms,
        "failureKind": None if reachable else (failure_kind or "http"),
    }


def _probe_platform(platform: str, timeout: float) -> dict[str, Any]:
    return probe_url(PROBES[platform], timeout=timeout)


def detect_network(timeout: float = 4.0) -> dict[str, Any]:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(_probe_platform, platform, timeout): platform
            for platform in PLATFORMS
        }
        for future in as_completed(futures):
            platform = futures[future]
            try:
                results[platform] = future.result()
            except Exception as error:
                results[platform] = {
                    "reachable": False,
                    "httpStatus": None,
                    "latencyMs": 0,
                    "failureKind": _failure_kind(error),
                }
    search_platforms = [
        platform for platform in PLATFORMS if results[platform]["reachable"]
    ]
    youtube_reachable = results["youtube"]["reachable"]
    bilibili_reachable = results["bilibili"]["reachable"]
    mode = "global" if youtube_reachable else "cn" if bilibili_reachable else "offline"
    return {
        "mode": mode,
        "checkedAt": utc_now(),
        "timeoutSeconds": timeout,
        "platformsToSearch": search_platforms,
        "platforms": results,
    }


def score_candidate(query: str, candidate: dict[str, Any]) -> tuple[float, list[str]]:
    query_terms = text_terms(query)
    title = clean_text(candidate.get("title"))
    tags = clean_text(candidate.get("tags"))
    description = clean_text(candidate.get("description"))
    author = clean_text(candidate.get("author"))
    title_terms = text_terms(title)
    tag_terms = text_terms(tags)
    description_terms = text_terms(description)

    title_coverage = (
        len(query_terms & title_terms) / max(1, len(query_terms))
        if query_terms
        else 0
    )
    tag_coverage = (
        len(query_terms & tag_terms) / max(1, len(query_terms))
        if query_terms
        else 0
    )
    description_coverage = (
        len(query_terms & description_terms) / max(1, len(query_terms))
        if query_terms
        else 0
    )

    combined = normalized(" ".join((title, tags, description, author)))
    query_parts = sorted(
        {
            part
            for part in (normalized(item).strip("？?。！!，,；;：:") for item in query.split())
            if len(part) >= 2
            and part not in STOP_TERMS
        }
    )
    title_exact_terms = [part for part in query_parts if part in normalized(title)]
    context_exact_terms = [
        part
        for part in query_parts
        if part not in title_exact_terms and part in combined
    ]
    positive_hits = sorted(term for term in POSITIVE_TERMS if term in combined)
    query_normalized = normalized(query)
    negative_hits = sorted(
        term
        for term in NEGATIVE_TERMS
        if term in combined and term not in query_normalized
    )
    trusted = next(
        (term for term in TRUSTED_CHANNEL_TERMS if term.casefold() in author.casefold()),
        None,
    )

    score = 0.0
    score += min(48.0, title_coverage * 70.0)
    score += min(14.0, tag_coverage * 24.0)
    score += min(8.0, description_coverage * 16.0)
    score += min(10.0, len(positive_hits) * 2.5)
    score += min(30.0, len(title_exact_terms) * 12.0)
    score += min(10.0, len(context_exact_terms) * 3.0)
    score -= min(55.0, len(negative_hits) * 22.0)
    if trusted:
        score += 8.0

    duration = candidate.get("durationSeconds")
    if isinstance(duration, int):
        if 60 <= duration <= 1_200:
            score += 8.0
        elif 30 <= duration < 60 or 1_200 < duration <= 2_400:
            score += 3.0
        elif duration < 20 or duration > 3_600:
            score -= 6.0

    views = (candidate.get("metrics") or {}).get("views")
    if isinstance(views, int) and views > 0:
        score += min(5.0, math.log10(views + 1) - 1.0)
    source_rank = candidate.get("sourceRank")
    if isinstance(source_rank, int) and source_rank > 0:
        score += max(0.0, 7.0 - source_rank * 0.35)

    reasons: list[str] = []
    if title_coverage:
        reasons.append(f"标题覆盖查询 {round(title_coverage * 100)}%")
    if positive_hits:
        reasons.append("教育性关键词：" + "、".join(positive_hits[:4]))
    if title_exact_terms:
        reasons.append("标题精确命中：" + "、".join(title_exact_terms[:4]))
    if context_exact_terms:
        reasons.append("标签或描述命中：" + "、".join(context_exact_terms[:4]))
    if trusted:
        reasons.append(f"可信讲解者信号：{trusted}")
    if isinstance(duration, int) and 60 <= duration <= 1_200:
        reasons.append("时长适合知识讲解")
    if negative_hits:
        reasons.append("降权关键词：" + "、".join(negative_hits[:4]))
    if not reasons:
        reasons.append("仅有基础文本相关度")
    return max(0.0, min(100.0, round(score, 1))), reasons


def canonical_video(candidate: dict[str, Any], query: str) -> dict[str, Any]:
    score, reasons = score_candidate(query, candidate)
    candidate["relevanceScore"] = score
    candidate["rankingReasons"] = reasons
    return candidate


def search_bilibili(query: str, timeout: float) -> list[dict[str, Any]]:
    url = (
        "https://api.bilibili.com/x/web-interface/search/type"
        f"?search_type=video&keyword={quote_plus(query)}&page=1"
    )
    body = b""
    last_error: BaseException | None = None
    for attempt in range(3):
        try:
            _, body = fetch_url(url, timeout, body=True)
            last_error = None
            break
        except HTTPError as error:
            last_error = error
            if error.code == 412 and attempt < 2:
                time.sleep(0.8 * (attempt + 1))
                continue
            break
        except (OSError, URLError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))
                continue
            break
    if last_error is not None:
        raise SearchError(
            "bilibili",
            f"Bilibili search failed: {last_error}",
        ) from last_error
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SearchError("bilibili", "Bilibili returned invalid JSON") from error
    if payload.get("code") != 0:
        raise SearchError(
            "bilibili",
            f"Bilibili search code {payload.get('code')}: {payload.get('message')}",
        )

    results: list[dict[str, Any]] = []
    for source_rank, item in enumerate(
        (payload.get("data") or {}).get("result") or [],
        start=1,
    ):
        if item.get("type") != "video" or not item.get("bvid"):
            continue
        bvid = str(item["bvid"])
        thumbnail = clean_text(item.get("pic"))
        if thumbnail.startswith("//"):
            thumbnail = f"https:{thumbnail}"
        published = None
        if isinstance(item.get("pubdate"), (int, float)):
            published = datetime.fromtimestamp(
                item["pubdate"], tz=timezone.utc
            ).date().isoformat()
        candidate = {
            "platform": "bilibili",
            "platformId": bvid,
            "title": clean_text(item.get("title")),
            "author": clean_text(item.get("author")),
            "url": f"https://www.bilibili.com/video/{bvid}",
            "embedUrl": (
                "https://player.bilibili.com/player.html"
                f"?bvid={bvid}&page=1&autoplay=0"
            ),
            "thumbnailUrl": thumbnail or None,
            "description": clean_text(item.get("description")),
            "tags": clean_text(item.get("tag")),
            "durationSeconds": parse_duration(item.get("duration")),
            "publishedAt": published,
            "metrics": {
                "views": parse_count(item.get("play")),
                "likes": parse_count(item.get("like")),
                "comments": parse_count(item.get("review")),
            },
            "sourceRank": source_rank,
        }
        results.append(canonical_video(candidate, query))
    return results


def _find_video_renderers(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"videoRenderer", "compactVideoRenderer"} and isinstance(child, dict):
                found.append(child)
            else:
                found.extend(_find_video_renderers(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_find_video_renderers(child))
    return found


def _runs_text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    if isinstance(value.get("simpleText"), str):
        return clean_text(value["simpleText"])
    runs = value.get("runs")
    if not isinstance(runs, list):
        return ""
    return clean_text("".join(str(run.get("text", "")) for run in runs if isinstance(run, dict)))


def _extract_yt_initial_data(source: str) -> dict[str, Any]:
    markers = (
        "var ytInitialData = ",
        "ytInitialData = ",
        'window["ytInitialData"] = ',
    )
    decoder = json.JSONDecoder()
    for marker in markers:
        start = source.find(marker)
        if start < 0:
            continue
        payload_start = start + len(marker)
        try:
            payload, _ = decoder.raw_decode(source[payload_start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise SearchError("youtube", "YouTube search page did not contain ytInitialData")


def search_youtube(query: str, timeout: float) -> list[dict[str, Any]]:
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    body = b""
    last_error: BaseException | None = None
    for attempt in range(3):
        try:
            _, body = fetch_url(url, timeout, body=True)
            last_error = None
            break
        except HTTPError as error:
            last_error = error
            if error.code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(0.7 * (attempt + 1))
                continue
            break
        except (OSError, URLError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(0.7 * (attempt + 1))
                continue
            break
    if last_error is not None:
        raise SearchError(
            "youtube",
            f"YouTube search failed: {last_error}",
        ) from last_error
    try:
        source = body.decode("utf-8", errors="replace")
    except Exception as error:
        raise SearchError("youtube", "Could not decode YouTube search page") from error
    payload = _extract_yt_initial_data(source)

    results: list[dict[str, Any]] = []
    for source_rank, item in enumerate(_find_video_renderers(payload), start=1):
        video_id = item.get("videoId")
        if not isinstance(video_id, str) or not re.fullmatch(r"[\w-]{6,}", video_id):
            continue
        title = _runs_text(item.get("title"))
        if not title:
            continue
        author = _runs_text(item.get("ownerText")) or _runs_text(
            item.get("longBylineText")
        )
        thumbnail_url = None
        thumbnails = (
            (item.get("thumbnail") or {}).get("thumbnails")
            if isinstance(item.get("thumbnail"), dict)
            else None
        )
        if isinstance(thumbnails, list) and thumbnails:
            thumbnail_url = thumbnails[-1].get("url")
        snippets = item.get("detailedMetadataSnippets")
        description = ""
        if isinstance(snippets, list) and snippets:
            description = _runs_text(
                (snippets[0] or {}).get("snippetText")
                if isinstance(snippets[0], dict)
                else None
            )
        candidate = {
            "platform": "youtube",
            "platformId": video_id,
            "title": title,
            "author": author,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{video_id}",
            "thumbnailUrl": thumbnail_url,
            "description": description,
            "tags": "",
            "durationSeconds": parse_duration(
                (item.get("lengthText") or {}).get("simpleText")
                if isinstance(item.get("lengthText"), dict)
                else None
            ),
            "publishedAt": None,
            "publishedLabel": _runs_text(item.get("publishedTimeText")),
            "metrics": {
                "views": parse_count(
                    (item.get("viewCountText") or {}).get("simpleText")
                    if isinstance(item.get("viewCountText"), dict)
                    else None
                ),
                "likes": None,
                "comments": None,
            },
            "sourceRank": source_rank,
        }
        results.append(canonical_video(candidate, query))
    return results


def search_platform(
    platform: str,
    query: str,
    timeout: float,
) -> list[dict[str, Any]]:
    if platform == "bilibili":
        return search_bilibili(query, timeout)
    if platform == "youtube":
        return search_youtube(query, timeout)
    raise ValueError(f"unknown platform: {platform}")


def deduplicate(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (candidate["platform"], candidate["platformId"])
        existing = unique.get(key)
        if existing is None or candidate["relevanceScore"] > existing["relevanceScore"]:
            unique[key] = candidate
    return list(unique.values())


def select_candidates(
    candidates: list[dict[str, Any]],
    limit: int,
    excluded_ids: set[str],
) -> list[dict[str, Any]]:
    filtered = [
        candidate
        for candidate in deduplicate(candidates)
        if candidate["platformId"] not in excluded_ids
        and candidate["relevanceScore"] >= 18
        and not any(
            term in " ".join(candidate["rankingReasons"])
            for term in SEVERE_NEGATIVE_TERMS
        )
    ]
    filtered.sort(
        key=lambda item: (
            item["relevanceScore"],
            (item.get("metrics") or {}).get("views") or 0,
            item.get("durationSeconds") or 0,
        ),
        reverse=True,
    )
    return filtered[:limit]


def make_query(content: dict[str, Any], node: dict[str, Any], fallback: bool) -> str:
    tags = [clean_text(tag) for tag in node.get("tags", []) if clean_text(tag)]
    topic = clean_text((content.get("meta") or {}).get("topic"))
    if fallback:
        parts = [topic, clean_text(node.get("label")), *tags]
        parts.append("科普 原理" if CJK_RUN_RE.search(topic) else "explained")
    else:
        parts = [
            clean_text(node.get("question")),
            *tags,
        ]
    return SPACE_RE.sub(" ", " ".join(part for part in parts if part)).strip()


def _run_search_batch(
    requests: list[tuple[str, str]],
    *,
    timeout: float,
) -> dict[tuple[str, str], tuple[list[dict[str, Any]], SearchError | None]]:
    unique_requests = list(dict.fromkeys(requests))
    if not unique_requests:
        return {}

    platforms = {platform for platform, _ in unique_requests}
    semaphores = {
        platform: threading.BoundedSemaphore(
            PLATFORM_CONCURRENCY.get(platform, 1)
        )
        for platform in platforms
    }
    max_workers = max(
        1,
        min(8, sum(PLATFORM_CONCURRENCY.get(platform, 1) for platform in platforms)),
    )

    def run(platform: str, query: str) -> tuple[list[dict[str, Any]], SearchError | None]:
        with semaphores[platform]:
            try:
                _pace_platform(platform)
                return search_platform(platform, query, timeout), None
            except SearchError as error:
                return [], error
            except Exception as error:
                return [], SearchError(platform, str(error))

    results: dict[
        tuple[str, str],
        tuple[list[dict[str, Any]], SearchError | None],
    ] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run, platform, query): (platform, query)
            for platform, query in unique_requests
        }
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()
    return results


def research_content(
    content: dict[str, Any],
    *,
    platforms: list[str],
    network: dict[str, Any],
    limit: int,
    timeout: float,
    node_ids: set[str] | None = None,
) -> dict[str, Any]:
    queried_at = date.today().isoformat()
    report_nodes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    excluded_ids: set[str] = set()

    node_specs: list[dict[str, Any]] = []
    for node in content.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        if node_ids and node_id not in node_ids:
            continue
        node_specs.append(
            {
                "node": node,
                "nodeId": node_id,
                "primaryQuery": make_query(content, node, fallback=False),
                "fallbackQuery": make_query(content, node, fallback=True),
            }
        )

    primary_requests = [
        (platform, spec["primaryQuery"])
        for spec in node_specs
        for platform in platforms
    ]
    primary_results = _run_search_batch(primary_requests, timeout=timeout)

    for spec in node_specs:
        node = spec["node"]
        node_id = spec["nodeId"]
        primary_query = spec["primaryQuery"]
        fallback_query = spec["fallbackQuery"]
        raw_candidates: list[dict[str, Any]] = []
        searches: list[dict[str, Any]] = []

        def apply_query(query: str, results: dict[tuple[str, str], tuple[list[dict[str, Any]], SearchError | None]]) -> None:
            for platform in platforms:
                found, error = results.get((platform, query), ([], SearchError(platform, "search did not run")))
                if error is None:
                    raw_candidates.extend(found)
                    searches.append(
                        {
                            "platform": platform,
                            "query": query,
                            "resultCount": len(found),
                            "status": "ok",
                        }
                    )
                else:
                    errors.append({"nodeId": node_id, **error.as_dict()})
                    searches.append(
                        {
                            "platform": platform,
                            "query": query,
                            "resultCount": 0,
                            "status": "error",
                            "message": error.message,
                        }
                    )

        apply_query(primary_query, primary_results)
        selected_preview = select_candidates(raw_candidates, limit, excluded_ids)
        if len(selected_preview) < min(3, limit):
            fallback_results = _run_search_batch(
                [(platform, fallback_query) for platform in platforms],
                timeout=timeout,
            )
            apply_query(fallback_query, fallback_results)

        selected = select_candidates(raw_candidates, limit, excluded_ids)
        candidates = []
        for rank, candidate in enumerate(selected, start=1):
            item = dict(candidate)
            item["rank"] = rank
            item["suggestedVideoLink"] = {
                "id": f"{node_id}-video-{rank}",
                "title": item["title"],
                "url": item["url"],
                "embedUrl": item["embedUrl"],
                "platform": item["platform"],
                "author": item["author"] or None,
                "thumbnailUrl": item.get("thumbnailUrl"),
                "durationSeconds": item.get("durationSeconds"),
                "publishedAt": item.get("publishedAt"),
                "queryDate": queried_at,
                "relevanceScore": item["relevanceScore"],
                "selectionRationale": "；".join(item["rankingReasons"]),
            }
            candidates.append(item)
            excluded_ids.add(item["platformId"])
        report_nodes.append(
            {
                "nodeId": node_id,
                "question": clean_text(node.get("question")),
                "queries": searches,
                "candidates": candidates,
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": utc_now(),
        "network": network,
        "ranking": {
            "method": "text relevance + educational intent + trusted channel + duration + light engagement",
            "limitPerNode": limit,
            "minimumScore": 12,
            "note": "候选分数用于缩小审阅范围，不替代对讲解内容和节点目标的最终判断。",
        },
        "nodes": report_nodes,
        "errors": errors,
    }


def load_content(path: Path) -> dict[str, Any]:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"file not found: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load JSON: {error}") from error
    if not isinstance(content, dict):
        raise ValueError("content must be a JSON object")
    if not isinstance(content.get("meta"), dict):
        raise ValueError("content.meta must be an object")
    if not isinstance(content.get("nodes"), list):
        raise ValueError("content.nodes must be an array")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path, help="AskWhy content JSON with planned nodes")
    parser.add_argument("--output", type=Path, help="Video research JSON output")
    parser.add_argument("--limit", type=int, default=5, help="Candidates per node (1–10)")
    parser.add_argument(
        "--platform",
        choices=(*PLATFORMS, "auto", "all"),
        default="auto",
        help="Platform policy; auto probes reachability once",
    )
    parser.add_argument("--node", action="append", default=[], help="Only search this node ID")
    parser.add_argument("--timeout", type=float, default=8.0, help="Network timeout in seconds")
    args = parser.parse_args()

    if not 1 <= args.limit <= 10:
        print("ERROR   --limit must be from 1 to 10", file=sys.stderr)
        return 1
    if args.timeout <= 0:
        print("ERROR   --timeout must be positive", file=sys.stderr)
        return 1
    try:
        content = load_content(args.content)
    except ValueError as error:
        print(f"ERROR   {error}", file=sys.stderr)
        return 1

    if args.platform == "auto":
        network = detect_network(timeout=min(args.timeout, 4.0))
        platforms = list(network["platformsToSearch"])
    else:
        network = detect_network(timeout=min(args.timeout, 4.0))
        platforms = list(PLATFORMS) if args.platform == "all" else [args.platform]

    if not platforms:
        print("ERROR   No video platform is reachable.", file=sys.stderr)
        print(json.dumps(network, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    node_ids = set(args.node) if args.node else None
    report = research_content(
        content,
        platforms=platforms,
        network=network,
        limit=args.limit,
        timeout=args.timeout,
        node_ids=node_ids,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Searched {len(report['nodes'])} nodes on {', '.join(platforms)}.")
        print(f"Video research: {args.output.resolve()}")
    else:
        print(output, end="")
    if report["errors"]:
        print(
            f"WARNING {len(report['errors'])} platform search error(s); see report.errors.",
            file=sys.stderr,
        )
    return 0 if report["nodes"] else 1


if __name__ == "__main__":
    sys.exit(main())
