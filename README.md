# Encontrador de publicaciones en grupos de Facebook

Script en Python para detectar publicaciones en grupos de Facebook que estén en la línea de **consultoría académica SAC**.

## Qué hace

- Consulta el feed de los grupos que configures (por ID).
- Filtra publicaciones por palabras clave (por defecto enfocadas a consultoría académica/tesis).
- Exporta coincidencias en `JSON` con enlace permanente y fecha.

## Importante

Este proyecto usa **Facebook Graph API** (no scraping). Para funcionar necesitas:

1. Una app de Meta.
2. Un token con permisos de lectura de grupos aprobados por Meta.
3. Acceso permitido a los grupos objetivo.

Si los permisos no están aprobados, Facebook devolverá error.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Copia `config.example.json` y ajusta:

- `access_token`: token de Graph API (o usa variable `FB_ACCESS_TOKEN`).
- `group_ids`: IDs de grupos a consultar.
- `keywords`: términos a detectar.

## Ejecución

```bash
python facebook_group_finder.py --config config.example.json --limit 30 --verbose
```

Salida por defecto: `resultados_facebook.json`.

## Estructura de salida

```json
{
  "generated_at": "2026-04-10T00:00:00Z",
  "total_matches": 2,
  "matches": [
    {
      "group_id": "123...",
      "post_id": "123_456",
      "created_time": "2026-04-09T22:10:01+0000",
      "permalink_url": "https://www.facebook.com/...",
      "message": "Busco asesoría de tesis..."
    }
  ]
}
```
