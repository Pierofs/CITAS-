#!/usr/bin/env python3
"""Buscador de publicaciones en grupos de Facebook usando Graph API.

Uso:
    python facebook_group_finder.py --config config.example.json --limit 50

Requisitos:
- Token válido de Facebook Graph API con permisos aprobados para leer grupos.
- IDs de grupos donde se permitirá la lectura.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import requests

GRAPH_API_BASE = "https://graph.facebook.com/v23.0"
DEFAULT_KEYWORDS = [
    "consultoría académica",
    "consultoria academica",
    "tesis",
    "asesoría de tesis",
    "asesoria de tesis",
    "trabajos universitarios",
    "investigación",
    "investigacion",
]


@dataclass
class MatchResult:
    group_id: str
    post_id: str
    created_time: str
    permalink_url: str
    message: str


class FacebookGroupFinder:
    def __init__(
        self,
        access_token: str,
        group_ids: list[str],
        keywords: list[str],
        api_version: str = "v23.0",
        timeout: int = 30,
    ) -> None:
        self.access_token = access_token
        self.group_ids = group_ids
        self.keywords = [k.lower() for k in keywords]
        self.timeout = timeout
        self.base_url = f"https://graph.facebook.com/{api_version}"

    def _request(self, endpoint: str, params: dict[str, str | int]) -> dict:
        params = {**params, "access_token": self.access_token}
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, params=params, timeout=self.timeout)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Error de Graph API ({response.status_code}) en {endpoint}: {response.text}"
            )
        return response.json()

    def _contains_keyword(self, text: str) -> bool:
        lower = text.lower()
        return any(keyword in lower for keyword in self.keywords)

    def fetch_posts(self, group_id: str, limit: int) -> Iterable[dict]:
        fields = "id,message,created_time,permalink_url"
        data = self._request(f"{group_id}/feed", {"fields": fields, "limit": limit})
        for post in data.get("data", []):
            yield post

    def find_matches(self, limit: int) -> list[MatchResult]:
        results: list[MatchResult] = []
        for group_id in self.group_ids:
            logging.info("Analizando grupo %s", group_id)
            try:
                posts = self.fetch_posts(group_id=group_id, limit=limit)
                for post in posts:
                    message = post.get("message", "")
                    if message and self._contains_keyword(message):
                        results.append(
                            MatchResult(
                                group_id=group_id,
                                post_id=post.get("id", ""),
                                created_time=post.get("created_time", ""),
                                permalink_url=post.get("permalink_url", ""),
                                message=message.strip().replace("\n", " "),
                            )
                        )
            except Exception as exc:  # noqa: BLE001
                logging.warning("No se pudo leer el grupo %s: %s", group_id, exc)
        return results


def load_config(path: Path) -> tuple[str, list[str], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    token = raw.get("access_token") or os.getenv("FB_ACCESS_TOKEN", "")
    if not token:
        raise ValueError(
            "Falta access_token. Agrégalo en el archivo de config o en FB_ACCESS_TOKEN."
        )

    group_ids = raw.get("group_ids", [])
    if not group_ids:
        raise ValueError("Debes proporcionar al menos un group_id en config.")

    keywords = raw.get("keywords", DEFAULT_KEYWORDS)
    return token, group_ids, keywords


def write_results(path: Path, matches: list[MatchResult]) -> None:
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_matches": len(matches),
        "matches": [match.__dict__ for match in matches],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Busca publicaciones de Facebook en grupos relacionados con consultoría académica."
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Ruta al archivo JSON de configuración.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("resultados_facebook.json"),
        help="Archivo de salida JSON.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Máximo de publicaciones por grupo a consultar.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra logs detallados.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    try:
        token, group_ids, keywords = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        logging.error("Configuración inválida: %s", exc)
        return 1

    finder = FacebookGroupFinder(
        access_token=token,
        group_ids=group_ids,
        keywords=keywords,
    )
    matches = finder.find_matches(limit=args.limit)
    write_results(args.output, matches)

    print(f"Se encontraron {len(matches)} publicaciones.")
    print(f"Resultados guardados en: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
