import os
import sys
import datetime
import boto3
import mariadb
# from mariadb.connector import pooling
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

begin_time = datetime.datetime.now()
print(datetime.datetime.now())

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

connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="pynative_pool",
                                                              pool_size=10,
                                                              pool_reset_session=True,
                                                              user=os.getenv('DBUser'),
                                                              password=os.getenv('DBPassword'),
                                                              host="127.0.0.1",
                                                              port=3306)

# Instantiate Cursor
# TODO: Use MySQLCursorRaw cursor for performance
def create_mariadb_connection():
    try:
        conn = mariadb.connect(
          user=os.getenv('DBUser'),
          password=os.getenv('DBPassword'),
          host="127.0.0.1",
          port=3306)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    return conn


def iter_row(cur, size=10):
    while True:
        rows = cur.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

def query_with_fetchmany(conn, cur2):
    try:
        cur = conn.cursor()
        cur.execute("SELECT bucket_name FROM database1.buckets WHERE bucket_name REGEXP '^image'")

        for row in iter_row(cur, 10):
            move_file(row[0], cur2)

            print(row)
        cur.close()
    except Exception as e:
        print(e)

    finally:
        conn.commit()
        conn.close()

def update_record(new_value, old_value, cur):
    sql = "UPDATE database1.buckets SET bucket_name = %s WHERE bucket_name = %s"
    val = (new_value, old_value)
    cur.execute(sql, val)
    connection2.commit()

def move_file(old_filename, cur):
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

if __name__ == "__main__":
    connection= connection_pool.get_connection()
    connection2 = connection_pool.get_connection()
    cur = connection2.cursor()
    query_with_fetchmany(connection, cur)

    print(datetime.datetime.now() - begin_time)

    cur.close()
    connection2.close()
