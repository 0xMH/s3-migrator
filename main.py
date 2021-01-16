import concurrent.futures
import datetime
import os
import sys
from time import sleep

import boto3
from dotenv import load_dotenv
import mysql
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


def delete_object(object_name):
    """ Delete S3 object from a Bucket

       Args:
           object_name (string): S3 object name.
    """
    s3.delete_object(Bucket=bucket_from, Key=object_name)


def delete_all_objects(move_results):
    """ Delete all the copied bucket from MariaDB.

       Args:
           conn (MySQLConnection): Mysql connection.
       Returns: Number of rows.
    """
    for k, v in move_results.items():
        delete_object(k)


def s3_objects_count(conn):
    """ Count number of objects with the old prefix in MariaDB

       Args:
           conn (MySQLConnection): Mysql connection.
       Returns: Number of rows.
    """
    cur = conn.cursor()
    query = "select count(*) from database1.buckets WHERE bucket_name REGEXP '^image'"
    cur.execute(query)
    rows = list(cur.fetchall())
    cur.close()
    # extract the count from query's tuple and return it
    return rows[0][0]


def query_with_paging(conn, offset):
    """ Pulls chunks of rows from MariaDB 

       Args:
           conn (MySQLConnection): Mysql connection.
           offset (int): Offset rows before beginning to return the rows.
       Returns (list): Chunks of MariaDB data.
    """
    cur = conn.cursor()
    query = """SELECT bucket_name FROM database1.buckets WHERE 
            bucket_name REGEXP '^image' LIMIT 10 OFFSET %d""" % offset
    cur.execute(query)
    rows = cur.fetchall()
    return ["%s" % x for x in rows]


def iter_row(connection):
    """ Implement Pagination over MariaDB

       Args:
           connection (MySQLConnection): Mysql connection.
       Returns (generator): returns a generator containing a specfied numbers of files.
    """
    rows_count = s3_objects_count(connection)
    for i in range(0, rows_count, 10):
        yield query_with_paging(connection, i)


def update_record(connection_pool, move_results):
    """Update the moved S3 Objects name in MariaDB

       Args:
           connection_pool (connection_pool): The reserved MariaDBl
           connection_pool.
           move_results (dict): S3 Buckets to be updated on MariaDB.
    """
    connected = False
    while not connected:
        try:
            connected = True
            conn = connection_pool.get_connection()
            cur = conn.cursor()
            for k, v in move_results.items():
                new_filename = 'avatar/' + "/".join(k.split('/')[1:])
                sql = "UPDATE database1.buckets SET bucket_name = %s WHERE bucket_name = %s"
                val = (new_filename, k)
                cur.execute(sql, val)
                # delete_object(k)
            cur.close()
            conn.commit()
            conn.close()
        except mysql.connector.errors.PoolError:
            print("Sleeping.. (Pool Error)")
            sleep(.5)
        except mysql.connector.errors.DatabaseError:
            print("Sleeping.. (Database Error)")
            sleep(.5)


def move_file(old_filename, cur):
    new_filename = 'avatar/' + "/".join(old_filename.split('/')[1:])
    print(old_filename)
    print(new_filename)
    s3.copy_object(
        ACL='public-read',
        Bucket=bucket_to,
        CopySource={'Bucket': bucket_from, 'Key': old_filename},
        Key=new_filename
    )

    update_record(new_filename, old_filename)
    delete_object(old_filename)


def move_file_without_update(old_filename):
    """ Move all S3 objects between Buckets.

       Args:
           old_filename (string): The names of the S3 object that needs be
           moved.
       Returns (dict): Return dictionary of the moved S3 object.
    """
    new_filename = 'avatar/' + "/".join(old_filename.split('/')[1:])
    s3.copy_object(
        ACL='public-read',
        Bucket=bucket_to,
        CopySource={'Bucket': bucket_from, 'Key': old_filename},
        Key=new_filename
    )
    return {old_filename: True}


def move_all_files(files):
    """ Move all S3 objects between Buckets.

       Args:
           files (list): The names of the S3 object that needs be moved.

       Returns (dict): Return dictionary of the moved S3 objects.
    """
    move_results = {}
    for one_file in files:
        results = move_file_without_update(one_file)
        move_results.update(results)
    return move_results

    # update_record(new_filename, old_filename, cur)
    # delete_object(old_filename)


def move_all_obj(move_file, sites):
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(move_file, sites)


def main():

    # TODO: Use MySQLCursorRaw cursor for performance
    connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool",
                                                  pool_size=32,
                                                  pool_reset_session=True,
                                                  user=os.getenv('DBUser'),
                                                  password=os.getenv(
                                                      'DBPassword'),
                                                  host=os.getenv('host'),
                                                  port=3306)
    connection = connection_pool.get_connection()

    futures_list = []
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for row in iter_row(connection):
            futures = executor.submit(move_all_files, row)
            futures_list.append(futures)

        for future in futures_list:
            try:
                result = future.result(timeout=60)
                # print(result)
                update_record(connection_pool, result)
                # delete_all_objects(result)
                results.append(result)
            except Exception as e:
                print(e)
                results.append(None)

    print(results)


if __name__ == "__main__":
    main()
    print(datetime.datetime.now() - begin_time)
