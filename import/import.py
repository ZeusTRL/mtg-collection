import io, json, zipfile, os
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values

MTGJSON_URL = os.getenv("MTGJSON_URL", "https://mtgjson.com/api/v5/AllPrintings.json.zip")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2000"))

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "mtg")
PGUSER = os.getenv("PGUSER", "mtg")
PGPASSWORD = os.getenv("PGPASSWORD", "mtgpass")

INSERT_SQL = """
INSERT INTO public.cards (
  uuid, name, set_code, set_name, number, rarity, colors, types, supertypes, subtypes,
  mana_cost, cmc, oracle_text, layout, scryfall_id, released_at, legalities, raw
)
VALUES %s
ON CONFLICT (uuid) DO UPDATE SET
  name = EXCLUDED.name,
  set_code = EXCLUDED.set_code,
  set_name = EXCLUDED.set_name,
  number = EXCLUDED.number,
  rarity = EXCLUDED.rarity,
  colors = EXCLUDED.colors,
  types = EXCLUDED.types,
  supertypes = EXCLUDED.supertypes,
  subtypes = EXCLUDED.subtypes,
  mana_cost = EXCLUDED.mana_cost,
  cmc = EXCLUDED.cmc,
  oracle_text = EXCLUDED.oracle_text,
  layout = EXCLUDED.layout,
  scryfall_id = EXCLUDED.scryfall_id,
  released_at = EXCLUDED.released_at,
  legalities = EXCLUDED.legalities,
  raw = EXCLUDED.raw;
"""

def parse_date(s):
    if not s: return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def main():
    print(f"Downloading MTGJSON: {MTGJSON_URL}")
    r = requests.get(MTGJSON_URL, timeout=600)
    r.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    json_name = [n for n in zf.namelist() if n.endswith(".json")][0]
    data = json.loads(zf.read(json_name).decode("utf-8"))
    sets = data.get("data", {})

    buf = []
    total = 0

    for set_code, set_obj in sets.items():
        set_name = set_obj.get("name")
        for c in set_obj.get("cards", []):
            uuid = c.get("uuid")
            if not uuid: continue
            row = (
                uuid,
                c.get("name"),
                set_code,
                set_name,
                c.get("number"),
                c.get("rarity"),
                c.get("colors") or None,
                c.get("types") or None,
                c.get("supertypes") or None,
                c.get("subtypes") or None,
                c.get("manaCost"),
                c.get("convertedManaCost") or c.get("cmc"),
                c.get("text") or c.get("originalText") or c.get("faceName") or None,
                c.get("layout"),
                (c.get("identifiers") or {}).get("scryfallId"),
                parse_date(c.get("releaseDate") or set_obj.get("releaseDate")),
                json.dumps(c.get("legalities") or {}),
                json.dumps({
                    "identifiers": c.get("identifiers", {}),
                    "printings": c.get("printings"),
                    "colorIdentity": c.get("colorIdentity"),
                    "edhrecRank": c.get("edhrecRank"),
                }),
            )
            buf.append(row)
            total += 1
            if len(buf) >= BATCH_SIZE:
                flush(buf); buf.clear()

    if buf: flush(buf)
    print(f"Imported/updated {total:,} cards.")

def flush(rows):
    conn = psycopg2.connect(
        host=PGHOST, port=PGPORT, dbname=PGDATABASE, user=PGUSER, password=PGPASSWORD
    )
    with conn, conn.cursor() as cur:
        execute_values(cur, INSERT_SQL, rows, page_size=len(rows))
    conn.commit()
    conn.close()
    print(f"Flushed {len(rows)} rows")

if __name__ == "__main__":
    main()
