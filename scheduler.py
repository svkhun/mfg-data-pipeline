import time
import schedule
import logging
from batch_etl import run_batch_etl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def job():
    logging.info("Triggering scheduled Batch ETL pipeline...")
    try:
        run_batch_etl()
    except Exception as e:
        logging.error(f"Scheduled job execution failed: {e}")

# กำหนดให้ทำงานทุกๆ 1 นาที (จำลองรอบ Batch สรุปข้อมูล)
schedule.every(1).minutes.do(job)

if __name__ == "__main__":
    # ติดตั้ง library schedule ก่อนใช้งาน: pip install schedule
    logging.info("Batch ETL Scheduler initialized. Running every 1 minute. (Press Ctrl+C to stop)")
    job() # รันทันที 1 รอบแรกเมื่อเริ่มทำงาน
    while True:
        schedule.run_pending()
        time.sleep(1)