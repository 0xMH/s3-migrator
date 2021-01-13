# Design Document

---
## Objective*
 Move several millions of images from S3 bucket to another bucket and change
 its prefix
# Possible Solution*

I thought of multiple paths to procced on:

### Using AWS Lambda function

We could create a Lambda function and invoke it from Amazon S3 batch
operations.S3 Batch Operations can invoke AWS Lambda functions to perform
custom actions on objects that are listed in a manifest. So one invoked function will
be responsible to first check if this single object indeed has the old `image/`
prefix if so It'll move from BucketA to BucketB and then update that object name in MariaDB. 

Pros:

 - This will be the fastest solution to move multi-millions files
 - We could invoke as much lambda as possible and move the objects concurrently
   without much of a limit.


Cons:
 - This will be a nightmare to our MariaDB database as for each lambda getting
   invoked it'll hit the database at least twice(one for checking if the file
   needs to be moved or not and another to update the file's state after
   actually moving it). So a large number of Lambdas running concurrently will
   be a huge problem here.
 - an inability to keep the state of the current invoked lambda batch without using an external service like Redis/S3/DynamoDb for example. If we Could do that we could've
   done that and used a bulk update to MariaDB.
 - Additional costs of lambda functions which will add up quickly as we're
   talking about millions of files here and extra cost of the other services
   that we need to use to keep the state.

### Using Two AWS Lambda function

We could hack the last approach a little by using two lambda functions instead of one.
This will make our setup more resilient to errors. The first lambda will be invoked with
S3 batch operation but the second one will run on event notifications from S3.
The second lambda will be responsible for updating MariaDB if the buckets received
a new object.

So The flow will be like this:

1. Lambda-1 get invoked with all files from BucketA and copy them one-by-one to
   Bucket-B in a loop after checking Dynamodb table and make sure they are not
   copied before.
2. In the same loop it also puts one entry in the DynamoDb table say
   "Copy_Logs" with column Key and Flag. Where Key is the object Key of the file and Flag is set to false telling the state of the copy operation.
3. Now configure events on BucketB to invoke a Lambda-2 on every put event
4. Now Lambda-2 will read the object key from S3 notification payload and
   updates its respective record in DynamoDb table with a flag set to true and
   rename it.
5. Now you have all records in DynamoDb table "Copy-Logs" which files were copied successfully and which were not. Now for actually changing the names of the files in our production MariaDB.
   We have two options:
        
   - Either We leave it to our second Lambda. It'll update these files' records
     in our production Mariadb and then remove it from BucketA.
   - Or We create a cron job that checks the DynamoDb table and **Bulk
     Load** the changes to MariaDB and then remove these files from BucketA.

Pros:
 - This is more resilient to errors than our first approach. Cause Files are
   not updated unless they get committed to BucketB and BucketB actually
   acknowledge it and invoke Lambda-2.
 - It's a production safe Cause we won't be overwhelming MariaDB with
   connections as much as the first approach.
 - It's Faster/Safer Than using any other CLI tool.

Cons:
 - Additional costs of the lambda functions which will add up quickly. Costs of
   DynamoDb and the Costs of S3 storage of the duplicated files between BucketA
   and BucketB till it gites removed with our cron job.
 - The Lambda-2 will be running all time time from all the files that get added to
   the BucketB either it's a copied files for new files added for the first
   time.

### Create a typical script 

We can create a small script that can do the job. By adding a little bit of
Concurrency and combining that with a moderate retrieval select by chunks from
the database and update our files by using the Bulk load. My guess Is that we can reach good
results By taking a slow but consistent approach.

The flow will be like this:

1. Read a chunk of old files from Mariadb.
2. Copying These files using AWS SDK from BucketA to BucketB.
3. Run multiple copying functions concurrently.
4. Note the results of the copying process.
5. Update MariaDB with the results and remove the successfully copied files. 
6. Rebeat.

Some PseudoCode:
// Read from Database
const LegacyFiles = DB.find({legacy: true, Limit=50})


// Functions for Copying the files
func Copy(ObjectName string) int {
    Copy the ObjectName from BucketA to BucketB

    return results of the copying process
}

// LegacyFiles
//   Fire a copy operations concurrently 
for files in LegacyFiles {
 go Copy(file)
}

Db.update(list of successfully copied files)

Pros:
 - Easier in the process of writing and implementation.
 - Won't overwhelm MariaDB with requests
 - Cheap no extra costs needed.

Cons:
- Slow.


## So Which approach to choose?

If The budget is not a problem and we want to move these files as fast as
possible I'll go with option two But if the time isn't an issue for us I'll go
with the third option.


