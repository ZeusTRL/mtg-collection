CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.cards (
  uuid UUID PRIMARY KEY,
  name TEXT NOT NULL,
  set_code TEXT NOT NULL,
  set_name TEXT NOT NULL,
  number TEXT,
  rarity TEXT,
  colors TEXT[] NULL,
  types TEXT[] NULL,
  supertypes TEXT[] NULL,
  subtypes TEXT[] NULL,
  mana_cost TEXT,
  cmc NUMERIC,
  oracle_text TEXT,
  layout TEXT,
  scryfall_id UUID,
  released_at DATE,
  legalities JSONB,
  raw JSONB
);

CREATE TABLE IF NOT EXISTS public.my_collection (
  id BIGSERIAL PRIMARY KEY,
  card_uuid UUID NOT NULL REFERENCES public.cards(uuid) ON DELETE CASCADE,
  quantity INTEGER NOT NULL DEFAULT 1,
  condition TEXT DEFAULT 'NM',
  language TEXT DEFAULT 'en',
  is_foil BOOLEAN DEFAULT FALSE,
  location TEXT,
  tags TEXT[],
  acquisition_price NUMERIC,
  notes TEXT,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cards_name ON public.cards USING gin (to_tsvector('simple', name));
CREATE INDEX IF NOT EXISTS idx_cards_set_code ON public.cards (set_code);
CREATE INDEX IF NOT EXISTS idx_cards_types ON public.cards USING gin (types);
CREATE INDEX IF NOT EXISTS idx_cards_colors ON public.cards USING gin (colors);
CREATE INDEX IF NOT EXISTS idx_mycol_card_uuid ON public.my_collection (card_uuid);
CREATE INDEX IF NOT EXISTS idx_mycol_tags ON public.my_collection USING gin (tags);
