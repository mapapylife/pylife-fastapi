-- Enable pg_trgm extension
-- This requires postgresql-contrib package to be installed!
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Table: map_index_houses
CREATE TABLE IF NOT EXISTS map_index_houses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tsv TSVECTOR NOT NULL,
    FOREIGN KEY (id) REFERENCES map_houses(id) ON DELETE CASCADE
);

-- Index: map_index_houses_tsv_idx
CREATE INDEX map_index_houses_tsv_idx
    ON map_index_houses USING gin(tsv);

-- Function: update_index_houses()
CREATE OR REPLACE FUNCTION update_index_houses() RETURNS trigger AS $$
DECLARE
    location_name text;
    new_name text;
    new_tsv tsvector;
BEGIN
    -- Check if row has changed or is new
    IF (OLD IS NULL OR OLD.title <> NEW.title OR OLD.location_id <> NEW.location_id) THEN
        SELECT name INTO location_name FROM map_zones WHERE id = NEW.location_id;

        -- Assign values from new row
        new_name := NEW.id || '. ' || NEW.title || ' (' || location_name || ')';
        new_tsv := to_tsvector('simple', new_name);

        -- Insert or update row in index table
        INSERT INTO map_index_houses (id, name, tsv)
            VALUES (NEW.id, new_name, new_tsv)
            ON CONFLICT (id)
            DO UPDATE SET name = new_name, tsv = new_tsv;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger: update_index_houses
CREATE TRIGGER update_index_houses
    AFTER INSERT OR UPDATE ON map_houses
    FOR EACH ROW
    EXECUTE FUNCTION update_index_houses();

-- Table: map_index_zones
CREATE TABLE IF NOT EXISTS map_index_zones (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tsv TSVECTOR NOT NULL,
    FOREIGN KEY (id) REFERENCES map_zones(id) ON DELETE CASCADE
);

-- Index: map_index_zones_tsv_idx
CREATE INDEX map_index_zones_tsv_idx
    ON map_index_zones USING gin(tsv);

-- Function: update_index_zones()
CREATE OR REPLACE FUNCTION update_index_zones() RETURNS trigger AS $$
DECLARE
    location_name text;
    new_name text;
BEGIN
    -- Check if row has changed or is new
    IF (OLD IS NULL OR OLD.name <> NEW.name OR OLD.root_id IS DISTINCT FROM NEW.root_id) THEN
        new_name := NEW.name;

        -- Append root zone name if exists
        IF (NEW.root_id IS NOT NULL) THEN
            SELECT name INTO location_name FROM map_zones WHERE id = NEW.root_id;
            new_name := new_name || ', ' || location_name;
        END IF;

        -- Insert or update row in index table
        INSERT INTO map_index_zones (id, name, tsv)
            VALUES (NEW.id, new_name, to_tsvector('simple', new_name))
            ON CONFLICT (id)
            DO UPDATE SET name = new_name, tsv = to_tsvector('simple', new_name);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger: update_index_zones
CREATE TRIGGER update_index_zones
    AFTER INSERT OR UPDATE ON map_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_index_zones();
