import os
import json
import httpx
import asyncio
import re
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
TIKTOK_USERNAMES    = os.environ["TIKTOK_USERNAMES"].split(",")   # e.g. "user1,user2"
STATE_FILE          = Path("seen_videos.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tiktok.com/",
}

# ── State helpers ─────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── TikTok scraper ────────────────────────────────────────────────────────────

async def fetch_latest_videos(username: str) -> list[dict]:
    """
    Fetches the latest videos from a TikTok profile page.
    Returns a list of dicts: {id, url, description, thumbnail, timestamp}
    """
    url = f"https://www.tiktok.com/@{username}"
    videos = []

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    # TikTok embeds initial data as JSON inside a <script> tag
    match = re.search(
        r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        print(f"[{username}] Could not find rehydration data.")
        return videos

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        print(f"[{username}] JSON parse error: {exc}")
        return videos

    # Navigate the nested structure to get the video list
    try:
        default_scope = data["__DEFAULT_SCOPE__"]
        user_page     = default_scope.get("webapp.user-detail", {})
        item_list     = user_page.get("itemList", [])

        # Fallback path used in some regions
        if not item_list:
            for key, val in default_scope.items():
                if "video-feed" in key or "user-post" in key:
                    item_list = val.get("itemList", [])
                    if item_list:
                        break
    except (KeyError, TypeError):
        print(f"[{username}] Unexpected data shape.")
        return videos

    for item in item_list[:10]:   # only look at the 10 most-recent videos
        try:
            video_id    = item["id"]
            description = item.get("desc", "")
            timestamp   = item.get("createTime", 0)
            thumb       = (item.get("video", {})
                               .get("cover", ""))
            video_url   = f"https://www.tiktok.com/@{username}/video/{video_id}"

            videos.append({
                "id":          video_id,
                "url":         video_url,
                "description": description,
                "thumbnail":   thumb,
                "timestamp":   timestamp,
            })
        except (KeyError, TypeError):
            continue

    return videos

# ── Discord notifier ──────────────────────────────────────────────────────────

async def send_discord_notification(username: str, video: dict):
    posted_at = datetime.utcfromtimestamp(video["timestamp"]).strftime("%d/%m/%Y %H:%M UTC") \
                if video["timestamp"] else "desconhecido"

    embed = {
        "title":       f"🎵 Novo vídeo de @{username}!",
        "url":         video["url"],
        "description": video["description"] or "_Sem descrição_",
        "color":       0xFF0050,   # TikTok pink
        "fields": [
            {"name": "📅 Publicado em", "value": posted_at, "inline": True},
            {"name": "🔗 Link",         "value": f"[Abrir no TikTok]({video['url']})", "inline": True},
        ],
        "footer": {"text": "TikTok Bot • via GitHub Actions"},
        "timestamp": datetime.utcnow().isoformat(),
    }

    if video["thumbnail"]:
        embed["thumbnail"] = {"url": video["thumbnail"]}

    payload = {
        "username":   "TikTok Bot",
        "avatar_url": "https://www.tiktok.com/favicon.ico",
        "embeds":     [embed],
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(DISCORD_WEBHOOK_URL, json=payload)
        if resp.status_code in (200, 204):
            print(f"  ✅  Notificação enviada: {video['url']}")
        else:
            print(f"  ❌  Discord respondeu {resp.status_code}: {resp.text}")

# ── Main loop ─────────────────────────────────────────────────────────────────

async def main():
    state = load_state()
    print(f"Verificando perfis: {TIKTOK_USERNAMES}")
    print(f"State atual: { {k: len(v) for k, v in state.items()} }")

    for username in TIKTOK_USERNAMES:
        username = username.strip()
        print(f"\n🔍 Buscando vídeos de @{username}…")

        try:
            videos = await fetch_latest_videos(username)
        except Exception as exc:
            print(f"  ⚠️  Erro ao buscar @{username}: {exc}")
            continue

        if not videos:
            print(f"  Nenhum vídeo encontrado para @{username}.")
            continue

        seen = set(state.get(username, []))
        new_videos = [v for v in videos if v["id"] not in seen]

        # Sort oldest-first so notifications appear in chronological order
        new_videos.sort(key=lambda v: v["timestamp"])

        print(f"  Encontrados {len(videos)} vídeos, {len(new_videos)} novos.")

        for video in new_videos:
            await send_discord_notification(username, video)
            seen.add(video["id"])
            await asyncio.sleep(1)   # avoid hitting Discord rate limits

        # Keep only the 50 most-recent IDs to prevent the file from growing forever
        all_ids = [v["id"] for v in videos] + list(seen)
        state[username] = list(dict.fromkeys(all_ids))[:50]

    save_state(state)
    print("\n✅ Concluído.")

if __name__ == "__main__":
    asyncio.run(main())
