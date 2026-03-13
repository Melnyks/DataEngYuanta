# Brokerage Data ETL Pipeline

ETL pipeline that processes brokerage CSV data (clients, instruments, trades)

## Required

- [Docker](https://www.docker.com/) and Docker Compose installed

## How to Start

1. Clone the repository:

```bash
git clone <repository-url>
cd DataEngYuanta
```

2. Start the services:

```bash
docker compose up --build
```

This will:

- Start a PostgreSQL database and create the schema via `init.sql`
- Build and start the ETL container
- Run the pipeline immediately, then repeat every 10 minutes

To stop the services:

```bash
docker compose down
```

To stop and **remove all data** (reset the database):

```bash
docker compose down -v
```

## How to Trigger a Run

### Periodic Mode (default)

```bash
docker compose up --build
```

The pipeline runs immediately on startup and then every 10 minutes automatically without manual intervention.

### On-Demand Mode (run once)

```bash
docker compose run etl python src/main.py --run-now
```

Runs the pipeline once and exits.

### Example SQL Queries

**Check row counts:**

```sql
SELECT 'clients' AS table_name, COUNT(*) FROM clients
UNION ALL
SELECT 'instruments', COUNT(*) FROM instruments
UNION ALL
SELECT 'trades', COUNT(*) FROM trades;
```

**View all trades sorted by time:**

```sql
SELECT * FROM trades ORDER BY trade_time;
```

**Check for missing references records:**

```sql
SELECT * FROM clients WHERE client_name = 'ANONYMOUS';
SELECT * FROM instruments WHERE symbol = 'UNKNOWN';
```

**Total trade volume per client:**

```sql
SELECT c.client_id, c.client_name, COUNT(*) AS total_trades, SUM(t.quantity * t.price) AS total_volume
FROM trades t
JOIN clients c ON t.client_id = c.client_id
GROUP BY c.client_id, c.client_name
ORDER BY total_volume DESC;
```

**Trades by side (BUY/SELL):**

```sql
SELECT side, COUNT(*) AS count, SUM(quantity * price) AS total_volume
FROM trades
GROUP BY side;
```

## Design Decisions and Trade-Offs

### Data Cleaning

- **ID normalization**: All IDs (`client_id`, `instrument_id`, `trade_id`) are stripped of whitespace and uppercased to handle inconsistent casing
- **Financial numbers**: Commas and quotes are removed from numeric fields (`price`, `fees`, `quantity`) and converted to float. Values that cannot be parsed become `NULL`.
- **Timestamps**: Timezone (`Z`) is removed from timestamps so they match the database format.
- **Duplicates**: Trades are sorted by `trade_time` and deduplicated by `trade_id`, keeping the latest entry. This handles late-arriving updates correctly.

### Referential Integrity

- Trades may reference clients or instruments not present in the reference data (e.g., `C999`, `I999`).
- Instead of dropping these trades, placeholder records are inserted with `client_name = 'ANONYMOUS'` and `symbol = 'UNKNOWN'`.
- Using explicit `UNKNOWN`/`ANONYMOUS` values instead of NULLs makes these easy to find in queries and reports.

### Upsert Pattern (Safe Re-Runs)

- Trades: loaded to a staging table first, then upserted into the trades table. If a trade already exists, it gets updated instead of causing an error.
- Clients & Instruments: skipped if already loaded.
- Result: the pipeline can run multiple times safely with the same outcome.

### Database Connection Retry

- The ETL container retries connecting to the database up to 5 times with 5-second intervals.
- This handles the case where the database container is still initializing when the ETL container starts.

### Scheduling

- The pipeline supports both on-demand (`--run-now`) and periodic (every 10 minutes) execution modes, controlled via command-line arguments.

## Project Structure

```
├── data/input/               # Source CSV files
│   ├── clients.csv
│   ├── instruments.csv
│   └── trades_2026-03-09.csv
├── src/
│   ├── main.py               # Main Function
│   ├── etl.py                # ETL pipeline logic
│   └── db.py                 # Database connection
├── init.sql                  # Database schema
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── CASE.md
└── README.md
```
