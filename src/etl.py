import pandas as pd
from sqlalchemy import text
from db import get_engine

def clean_financial_number(col):
    # remove comma ,quote and convert to numeric
    return pd.to_numeric(
        col.astype(str).str.replace(',', '', regex=False).str.replace('"', '', regex=False), 
        errors='coerce' 
    )

def ensure_referential_integrity(engine, df_trades):
    # Find missing clients
    existing_clients = pd.read_sql("SELECT client_id FROM clients", engine)['client_id'].tolist()
    missing_clients = df_trades[~df_trades['client_id'].isin(existing_clients)]['client_id'].unique()
    
    if len(missing_clients) > 0:
        no_data_clients = pd.DataFrame({
            'client_id': missing_clients,
            'client_name': 'ANONYMOUS',
            'kyc_status': 'UNKNOWN'
        })
        no_data_clients.to_sql('clients', engine, if_exists='append', index=False)

    # Find missing instruments
    existing_instruments = pd.read_sql("SELECT instrument_id FROM instruments", engine)['instrument_id'].tolist()
    missing_instruments = df_trades[~df_trades['instrument_id'].isin(existing_instruments)]['instrument_id'].unique()
    
    if len(missing_instruments) > 0:
        no_data_instruments = pd.DataFrame({
            'instrument_id': missing_instruments,
            'symbol': 'UNKNOWN',
            'asset_class': 'UNKNOWN'
        })
        no_data_instruments.to_sql('instruments', engine, if_exists='append', index=False)

def upsert_trades(engine, df_trades):
    # Load to temp staging table
    staging_table = 'trades_staging'
    df_trades.to_sql(staging_table, engine, if_exists='replace', index=False)
    
    # Execute the UPSERT 
    upsert_query = text("""
        INSERT INTO trades (trade_id, trade_time, client_id, instrument_id, side, quantity, price, fees, status)
        SELECT trade_id, trade_time, client_id, instrument_id, side, quantity, price, fees, status
        FROM trades_staging
        ON CONFLICT (trade_id) DO UPDATE SET
            trade_time = EXCLUDED.trade_time,
            client_id = EXCLUDED.client_id,
            instrument_id = EXCLUDED.instrument_id,
            side = EXCLUDED.side,
            quantity = EXCLUDED.quantity,
            price = EXCLUDED.price,
            fees = EXCLUDED.fees,
            status = EXCLUDED.status,
            processed_at = CURRENT_TIMESTAMP;
    """)
    
    with engine.begin() as conn:
        conn.execute(upsert_query)
        # Drop staging table
        conn.execute(text(f"DROP TABLE {staging_table}"))
        
    print(f"Successfully upserted {len(df_trades)} trades.")

def process_pipeline():
    engine = get_engine()
    
    # Load Clients and Instruments Data
    print("Loading Clients and Instruments Data")
    df_clients = pd.read_csv('data/input/clients.csv')
    df_instruments = pd.read_csv('data/input/instruments.csv')
    
    df_clients['client_id'] = df_clients['client_id'].astype(str).str.strip().str.upper()
    df_instruments['instrument_id'] = df_instruments['instrument_id'].astype(str).str.strip().str.upper()
    
    try:
        df_clients.to_sql('clients', engine, if_exists='append', index=False)
        df_instruments.to_sql('instruments', engine, if_exists='append', index=False)
    except Exception as e:
        print("Loading data Clients and Instruments failed")

    # Load Trades Data and clean
    print("Loading Trades Data")
    df_trades = pd.read_csv('data/input/trades_2026-03-09.csv')
    
    df_trades['client_id'] = df_trades['client_id'].astype(str).str.strip().str.upper()
    df_trades['instrument_id'] = df_trades['instrument_id'].astype(str).str.strip().str.upper()
    df_trades['trade_id'] = df_trades['trade_id'].astype(str).str.strip().str.upper()
    df_trades['price'] = clean_financial_number(df_trades['price'])
    df_trades['fees'] = clean_financial_number(df_trades['fees'])
    df_trades['quantity'] = clean_financial_number(df_trades['quantity']) 
    df_trades['side'] = df_trades['side'].astype(str).str.strip().str.upper()
    df_trades['trade_time'] = pd.to_datetime(df_trades['trade_time']).dt.tz_localize(None)
    df_trades = df_trades.sort_values('trade_time').drop_duplicates(subset=['trade_id'], keep='last')

    # Handle FK
    ensure_referential_integrity(engine, df_trades)

    # Load Trades
    upsert_trades(engine, df_trades)
    print("ETL Pipeline completed successfully")

if __name__ == "__main__":
    process_pipeline()