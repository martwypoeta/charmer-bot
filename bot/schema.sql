CREATE TABLE IF NOT EXISTS ss_grants
(
    user_id
    BIGINT
    PRIMARY
    KEY,
    granted_by
    BIGINT
);

CREATE TABLE IF NOT EXISTS reminders
(
    user_id
    BIGINT,
    message_id
    BIGINT,
    channel_id
    BIGINT,
    message
    TEXT,
    remind_time
    BIGINT
);
