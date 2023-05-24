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
        new_tsv := to_tsvector('simple', NEW.id || ' ' || NEW.title || ' ' || location_name);

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
BEGIN
    -- Check if row has changed or is new
    IF (OLD IS NULL OR OLD.name <> NEW.name) THEN
        -- Insert or update row in index table
        INSERT INTO map_index_zones (id, name, tsv)
            VALUES (NEW.id, NEW.name, to_tsvector('simple', NEW.name))
            ON CONFLICT (id)
            DO UPDATE SET name = NEW.name, tsv = to_tsvector('simple', NEW.name);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger: update_index_zones
CREATE TRIGGER update_index_zones
    AFTER INSERT OR UPDATE ON map_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_index_zones();
