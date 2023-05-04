CREATE TABLE IF NOT EXISTS watch_list (
    site_id bigserial,
    url varchar(128) not null,
    regexp varchar(32) not null,
    check_interval_sec smallint not null
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique__watch_list__site_id on watch_list(site_id);

CREATE TABLE IF NOT EXISTS metrics (
    site_id bigint not null references watch_list(site_id),
    "timestamp" timestamp with time zone not null,
    response_time bigint not null,
    status_code smallint not null,
    content varchar(256)
);

CREATE INDEX IF NOT EXISTS idx__metrics__site_id__timestamp on metrics(site_id, "timestamp");