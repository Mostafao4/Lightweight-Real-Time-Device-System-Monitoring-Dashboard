import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv("DATABASE_URL","sqlite:///monitor.db")
print("DB_URL =", db_url)
eng = create_engine(db_url, future=True)
with eng.connect() as c:
    try:
        total = c.execute(text("select count(*) from check_results")).scalar_one()
        print("check_results total:", total)
        rows = c.execute(text("""
            select d.id, d.name, d.host,
                   (select status from check_results cr
                    where cr.device_id=d.id
                    order by cr.created_at desc
                    limit 1) as latest_status
            from devices d order by d.id
        """)).all()
        for r in rows: print(r)
    except Exception as e:
        print("ERROR:", e)