import concurrent.futures
import csv
import datetime
import json
import logging
import os
import queue
import re
import threading
from time import sleep

import boto3
import botocore
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import mysql
from mysql.connector import pooling


begin_time = datetime.datetime.now()
load_dotenv()

aws_access_key_id = os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
bucket_from = os.getenv('bucket_from')
bucket_to = os.getenv('bucket_to')

client_config = botocore.config.Config(
    max_pool_connections=50,
)

s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    config=client_config
)


# Set up our logger
format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format)
logger = logging.getLogger()


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
    if rows_count == 0:
        logger.info(
            ' Cant find any object on Database. All objects are moved to Bucket %s', bucket_to)
        exit()
    logger.info(
        'Found %s Objects on database. Starting the moving process', rows_count)

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
            # Looping on {'filename': Bool}
            for k, v in move_results.items():
                if v:
                    new_filename = 'avatar/' + "/".join(k.split('/')[1:])
                    logger.info(
                        "Updating S3 object record  %s on database to %s.", k, new_filename)
                    sql = "UPDATE database1.buckets SET bucket_name = %s WHERE bucket_name = %s"
                    val = (new_filename, k)
                    cur.execute(sql, val)
                    # delete_object(k)
            cur.close()
            conn.commit()
            conn.close()
        except mysql.connector.errors.PoolError:
            logger.error(
                "Could not acquire database connection from ConnectionPool. Tring again...")
            sleep(0.2)
        except mysql.connector.errors.DatabaseError:
            logger.error(
                "Could not connect to server: Connection refused.  Trying again...")
            sleep(0.2)


def move_file_without_update(old_filename):
    """ Move all S3 objects between Buckets.

       Args:
           old_filename (string): The names of the S3 object that needs be
           moved.
       Returns (dict): Return dictionary of the moved S3 object.
    """
    new_filename = 'avatar/' + "/".join(old_filename.split('/')[1:])
    try:
        copy_result = s3.copy_object(
            ACL='public-read',
            Bucket=bucket_to,
            CopySource={'Bucket': bucket_from, 'Key': old_filename},
            Key=new_filename
        )

        """
         If the error occurs during the copy operation, the error response is embedded in the 200 OK response. 
         This means that a 200 OK response can contain either a success or an error.
        """
        if copy_result['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info('Copying object {}'.format(old_filename))
            if len(copy_result['CopyObjectResult']) == 0:
                logger.error("{}{}{}".format(
                    'InternalError:', 'Object: ' + old_filename,
                    ' not copied,  S3 aborted request'))
                return {old_filename: False}
            if re.search('err|Err', json.dumps(copy_result, indent=4, sort_keys=True, default=str)):
                logger.error("{}{}{}".format(
                    'InternalError:', 'Object: ' + old_filename,
                    ' not copied,  S3 aborted request'))
                return {old_filename: False}
        elif copy_result['ResponseMetadata']['HTTPStatusCode'] != 200:
            logger.error("{}{}{}".format(
                'InternalError:', 'Object: ' + old_filename,
                ' not copied,  S3 aborted request'))
            return {old_filename: False}

        logger.info('Object %s is successfully copied', old_filename)
        return {old_filename: True}
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            logger.warning("No object with name %s found on bucket %s",
                           old_filename, bucket_from)
            logger.warning("Object %s is not copied", old_filename)
            return {old_filename: False}
        if error.response['Error']['Code'] == 'NoSuchBucket':
            logger.error("Please specify a valid bucket names")
            raise error


def move_all_objs(files):
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


class ProcessThread(threading.Thread):
    """
    Worker class that does extra proccess on the copying results
    """

    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            path = self.in_queue.get()
            result = self.process(path)
            self.out_queue.put(result)
            self.in_queue.task_done()

    @staticmethod
    def process(path):
        # Do the processing job here
        # delete_object(path)
        return path


class PrintThread(threading.Thread):
    """
    Class for writing results to a csv file
    """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def printfiles(self, p):
        # print(p, file=open("output.txt", "a"))
        with open('dit.csv', 'a') as f:
            writer = csv.DictWriter(f, fieldnames=['Object', 'Status'])
            writer.writeheader()
            writer.writerow(p)

    def run(self):
        while True:
            result = self.queue.get()
            self.printfiles(result)
            self.queue.task_done()


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
    objectsqueue = queue.Queue()
    resultqueue = queue.Queue()

    # spawn threads to process
    workers_number = 20
    logger.info('spawning %s to workers to delele and update objects',
                workers_number)
    for _ in range(0, workers_number):
        worker = ProcessThread(objectsqueue, resultqueue)
        worker.setDaemon(True)
        worker.start()

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        for row in iter_row(connection):
            futures = executor.submit(move_all_objs, row)
            futures_list.append(futures)

        for future in futures_list:
            try:
                result = future.result(timeout=60)
                # update_record(connection_pool, result)
                # delete_all_objects(result)
                # results.append(result)
                for k, v in result.items():
                    objectsqueue.put({'Object': k, 'Status': v})
            except Exception as e:
                print(e)
                # results.append(None)

    # spawn threads to print
    worker = PrintThread(resultqueue)
    worker.setDaemon(True)
    worker.start()

    # wait for queue to get empty
    objectsqueue.join()
    resultqueue.join()


if __name__ == "__main__":
    main()
    logger.info('Finished on %s', datetime.datetime.now() - begin_time)
