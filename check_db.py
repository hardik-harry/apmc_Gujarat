import mysql.connector

conn = mysql.connector.connect(
    host='localhost', user='root', password='', database='apmc_ahmedabad'
)
c = conn.cursor()

# Check if there are case/space variations in commodity names
c.execute("""
    SELECT DISTINCT commodity_name 
    FROM commodities 
    WHERE LOWER(TRIM(commodity_name)) LIKE 'bhinda%'
""")
print("Variations of BHINDA:", c.fetchall())

# Check how many unique distinct commodity names exist
c.execute("SELECT COUNT(DISTINCT commodity_name) FROM commodities")
print("Distinct commodity names:", c.fetchone())

# How many commodity names have id > 0 vs id = 0
c.execute("SELECT id > 0 as has_real_id, COUNT(*) FROM commodities GROUP BY id > 0")
print("ID breakdown:", c.fetchall())

# Check if all commodity names actually map to matching ids in daily_rates
c.execute("""
    SELECT c.commodity_name, MIN(c.id) as min_id, 
           (SELECT COUNT(*) FROM daily_rates WHERE commodity_id = MIN(c.id)) as records
    FROM commodities c 
    WHERE c.id > 0
    GROUP BY c.commodity_name
    HAVING records = 0
    LIMIT 10
""")
print("Commodities with 0 matching records in daily_rates:", c.fetchall())

conn.close()
