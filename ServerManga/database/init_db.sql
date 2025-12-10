CREATE TABLE IF NOT EXISTS page_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    base_url TEXT,
    checker_script_path TEXT,
    downloader_script_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_page_type_name ON page_types(name);

CREATE TABLE IF NOT EXISTS manga (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    check_url TEXT NOT NULL,
    last_checked_chapter TEXT,
    current_chapter TEXT,
    current_reading TEXT,
    tracking INTEGER DEFAULT 1,
    page_type_id INTEGER NOT NULL,
    local_storage_path TEXT NOT NULL,
    last_check_timestamp DATETIME,
    olympus_index_url TEXT,
    last_download_url TEXT,
    slug TEXT,
    olympus_net_post_id INTEGER,
    FOREIGN KEY (page_type_id) REFERENCES page_types(id)
);

CREATE INDEX IF NOT EXISTS idx_page_type ON manga(page_type_id);
CREATE INDEX IF NOT EXISTS idx_last_check ON manga(last_check_timestamp);
CREATE INDEX IF NOT EXISTS idx_tracking ON manga(tracking);


CREATE TABLE IF NOT EXISTS olympus_com_cache (
    manga_id INTEGER PRIMARY KEY,
    last_search_asc_page INTEGER NOT NULL,
    last_search_desc_page INTEGER NOT NULL,
    olympus_last_valid_direction TEXT NOT NULL CHECK(olympus_last_valid_direction IN ('asc', 'desc')),
    FOREIGN KEY (manga_id) REFERENCES manga(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_olympus_cache_manga ON olympus_com_cache(manga_id);