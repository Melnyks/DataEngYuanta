CREATE TABLE IF NOT EXISTS clients (
    client_id VARCHAR(50) PRIMARY KEY,
    client_name VARCHAR(255),
    country VARCHAR(10),
    kyc_status VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instruments (
    instrument_id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(50),
    asset_class VARCHAR(50),
    currency VARCHAR(10),
    exchange VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id VARCHAR(50) PRIMARY KEY,
    trade_time TIMESTAMP,
    client_id VARCHAR(50),
    instrument_id VARCHAR(50),
    side VARCHAR(10),
    quantity NUMERIC,
    price NUMERIC,
    fees NUMERIC,
    status VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);