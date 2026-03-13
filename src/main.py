import sys
import time
import schedule
from etl import process_pipeline

def job():
    print(f"\n--- Starting Scheduled Pipeline Run at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    try:
        process_pipeline()
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    # run immediately
    if len(sys.argv) > 1 and sys.argv[1] == '--run-now':
        print("Running pipeline on-demand...")
        job()
    else:
        # run immediately and every 10 minutes
        print("Starting pipeline in periodic mode (runs every 10 minutes)...")
        job()
        
        schedule.every(10).minutes.do(job)
        
        while True:
            schedule.run_pending()
            time.sleep(1)