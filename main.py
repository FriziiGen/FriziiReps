from telethon import TelegramClient
from telethon.errors import FloodWaitError
import asyncio
import json
import os
import re

api_id = 23546939
api_hash = "109401a1a243d7481769122ea4a18e12"

ancien_canal = "litbuyfind"
nouveau_canal = "friziireps"

MOT_CLE = "litbuy"
FICHIER_PROGRESS = "progress.json"

client = TelegramClient("session_copie", api_id, api_hash)

def remplacer_texte(texte):
    if not texte:
        return ""

    texte = re.sub("ALF40", "FRIZII", texte, flags=re.IGNORECASE)
    texte = re.sub("CRZ20", "frizii", texte, flags=re.IGNORECASE)
    texte = texte.replace("2083666", "2255768")

    return texte

def charger_progression():
    if os.path.exists(FICHIER_PROGRESS):
        with open(FICHIER_PROGRESS, "r", encoding="utf-8") as f:
            return json.load(f).get("dernier_message_id", 0)
    return 0

def sauvegarder_progression(message_id):
    with open(FICHIER_PROGRESS, "w", encoding="utf-8") as f:
        json.dump({"dernier_message_id": message_id}, f)

def recuperer_contenu_album(album):
    contenu = ""

    for m in album:
        if m.text:
            contenu += m.text.lower() + " "

        if m.buttons:
            for row in m.buttons:
                for button in row:
                    url = getattr(button, "url", None)
                    if url:
                        contenu += url.lower() + " "

    return contenu

async def envoyer_album(album):
    if not album:
        return False

    album.sort(key=lambda x: x.id)

    contenu = recuperer_contenu_album(album)

    if MOT_CLE not in contenu:
        print("Ignoré : pas de litbuy")
        return False

    files = [m.media for m in album if m.media]

    if not files:
        return False

    caption_originale = next((m.text for m in album if m.text), "")
    caption_modifiee = remplacer_texte(caption_originale)

    while True:
        try:
            await client.send_file(
                nouveau_canal,
                files,
                caption=caption_modifiee
            )

            print("Album envoyé")
            return True

        except FloodWaitError as e:
            print(f"FloodWait détecté : attente de {e.seconds} secondes")
            await asyncio.sleep(e.seconds + 10)

        except Exception as e:
            print("Erreur pendant l'envoi :", e)
            return False

async def main():
    print("Démarrage sans délai entre albums...")

    dernier_message_id = charger_progression()

    if dernier_message_id:
        print(f"Reprise après ID : {dernier_message_id}")

    album_actuel_id = None
    album_actuel = []

    async for msg in client.iter_messages(
        ancien_canal,
        reverse=True,
        min_id=dernier_message_id
    ):

        if not msg.grouped_id:
            continue

        if album_actuel_id is None:
            album_actuel_id = msg.grouped_id
            album_actuel = [msg]
            continue

        if msg.grouped_id == album_actuel_id:
            album_actuel.append(msg)
            continue

        await envoyer_album(album_actuel)

        dernier_id_album = max(m.id for m in album_actuel)
        sauvegarder_progression(dernier_id_album)

        album_actuel_id = msg.grouped_id
        album_actuel = [msg]

    if album_actuel:
        await envoyer_album(album_actuel)

        dernier_id_album = max(m.id for m in album_actuel)
        sauvegarder_progression(dernier_id_album)

    print("Terminé")

with client:
    client.loop.run_until_complete(main())