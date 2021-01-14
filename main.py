import datetime
begin_time = datetime.datetime.now()
print(datetime.datetime.now())
import boto3
import mariadb
import os
import sys
from dotenv import load_dotenv

load_dotenv()

aws_access_key_id = os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
bucket_from = os.getenv('bucket_from')
bucket_to = os.getenv('bucket_to')

s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)


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
# src = s3.Bucket(bucket_from)

def iter_row(cur, size=10):
    while True:
        rows = cur.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

def query_with_fetchmany(cur):
    try:
        cur.execute("SELECT bucket_name FROM database1.buckets WHERE bucket_name REGEXP '^image'")

        contacts = []
        for row in iter_row(cur, 10):
            # contacts.append(row[0])
            print('This is the row', row[0])
            move_files(row[0], cur)

        print(contacts)
    except Exception as e:
        print(e)

    finally:
        cur.close()
        conn.close()


def update_record( new_value, old_value, cur):
    sql = "UPDATE database1.buckets SET bucket_name = %s WHERE bucket_name = %s"
    val = (new_value, old_value)
    cur.execute(sql, val)
    conn.commit()


def move_files(old_filename, cur):
        new_filename='avatar/'+ old_filename.split('/')[-1]
        print(old_filename)
        print(new_filename)
        s3.copy_object(
            ACL='public-read',
            Bucket=bucket_to,
            CopySource={'Bucket': bucket_from, 'Key': old_filename},
            Key=new_filename
        )
        update_record(new_filename, old_filename, cur)


# move_files()
query_with_fetchmany(cur)
print(datetime.datetime.now() - begin_time)
