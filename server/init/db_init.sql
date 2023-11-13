CREATE TABLE meta_basic (
    task_id VARCHAR(255),
    name VARCHAR(255),
    duration DECIMAL(6,2)
);

CREATE TABLE meta_advanced (
    task_id VARCHAR(255),
    result BLOB
);

SET wait_timeout = 60;

SET_GLOBAL max_connections = 1000;