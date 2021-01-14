import boto3
import mariadb
import os
import sys
from dotenv import load_dotenv

from pathlib import Path  
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

try:
    conn = mariadb.connect(
      user=os.getenv('DBUser'),
      password=os.getenv('DBPassword'),
      host="127.0.0.1",
      port=3306)
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

# Instantiate Cursor
cur = conn.cursor()


def add_multiple_Buckets(cur, data):
   """Adds multiple buckets to database from given data"""

   cur.executemany("INSERT INTO database1.buckets(bucket_name) VALUES (?)",
      data)
    
buckets= []

directory = os.fsencode("Buckets/oldBucket/image")
for file in os.listdir(directory):
     filename = os.fsdecode(file)
     buckets.append(('image/'+filename,))

print(buckets)
add_multiple_Buckets(cur, buckets)
conn.commit()
conn.close()
