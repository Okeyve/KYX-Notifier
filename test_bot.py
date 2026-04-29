"""
test_bot.py — Modo de teste: envia uma notificação no Discord para o vídeo
mais recente de cada perfil, SEM alterar o seen_videos.json.

Uso:
    python test_bot.py
"""

import asyncio
import os
from bot import fetch_latest_videos, send_discord_notification
import httpx
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
TIKTOK_USERNAMES    = os.environ["TIKTOK_USERNAMES"].split(",")


async def send_test_banner():
    """Envia uma mensagem de aviso antes dos embeds de teste."""
    payload = {
        "username":   "TikTok Bot",
        "avatar_url": "https://www.tiktok.com/favicon.ico",
        "embeds": [{
            "title":       "🧪 Modo de Teste Ativado",
            "description": (
                "As notificações abaixo são **apenas um teste**.\n"
                "O vídeo mais recente de cada perfil será exibido para confirmar que o bot está funcionando.\n"
                "O estado (`seen_videos.json`) **não será alterado**."
            ),
            "color": 0xFFA500,
            "footer": {"text": "TikTok Bot • Teste manual"},
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(DISCORD_WEBHOOK_URL, json=payload)


async def main():
    print("🧪 Modo de teste — nenhum estado será alterado.\n")
    await send_test_banner()
    await asyncio.sleep(1)

    for username in TIKTOK_USERNAMES:
        username = username.strip()
        print(f"🔍 Buscando vídeos de @{username}…")

        try:
            videos = await fetch_latest_videos(username)
        except Exception as exc:
            print(f"  ❌ Erro ao buscar @{username}: {exc}")
            continue

        if not videos:
            print(f"  ⚠️  Nenhum vídeo encontrado para @{username}.")
            continue

        latest = videos[0]
        print(f"  ✅ Vídeo mais recente encontrado: {latest['url']}")
        await send_discord_notification(username, latest)
        await asyncio.sleep(1)

    print("\n✅ Teste concluído. Verifique o canal do Discord!")


if __name__ == "__main__":
    asyncio.run(main())
