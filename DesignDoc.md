# Design Document

## Objective
 Move several millions of images from S3 bucket to another bucket and change
 its prefix.

## Possible Solutions:

- ### Single AWS Lambda Function

We shall rely on Lambda functions for this method as they can be invoked from Amazon S3 batch operations to perform custom actions on objects that are listed in a manifest. The function will be responsible to first check if an object contains `bucket-a/` prefix if so It'll move from Bucket-A to Bucket B and then update that object name in MariaDB. 

Pros:

 - This will be the fastest solution to move millions of files.
 - We could invoke as much lambda as possible and move the objects concurrently
   without much of a limit.


Cons:
 - This will be a nightmare to our MariaDB database as for each lambda getting
   invoked it'll hit the database at least twice(one for checking if the file
   needs to be moved or not and another to update the file's state after
   actually moving it). So, a large number of Lambdas running concurrently will
   be a huge problem here.
 - An inability to keep the state of the current invoked lambda batch without using an external service like Redis/S3/DynamoDb for example. If we could do that we could've
   done that and used a bulk update to MariaDB.
 - Additional costs of lambda functions which will add up quickly as we're
   talking about millions of files here and extra cost of the other services
   that we need to use to keep the state.

- ### Double AWS Lambda Functions

We could improve upon the previous approach a little by using two lambda functions instead of one.

This will make our setup more resilient to errors. The first lambda will be invoked with
S3 batch operation and the second one will run on event notifications from S3 which will be responsible for updating MariaDB if the buckets received a new object.

So The flow will be like this:

1. Lambda-1 gets invoked with all files from Bucket-A and copies them
   over to Bucket-B one by one, in a loop, after checking DynamoDB table and ensuring they are not copied before.
2. In the same iteration, it also inserts one entry in the DynamoDB table named
   "Copy_Logs" with column Key and Flag. Where Key is the object Key of the file and Flag is set to false telling the state of the copy operation.
3. Configure events on Bucket-B to listen for put events on Lambda-2. 
4. Lambda-2 reads the object key from S3 notification payload and
   updates its respective record in DynamoDb table setting the flag to true and
   renames it.
5. Changing the names of the files in our production MariaDB. We have two options:
        
   - Leave it to our second Lambda. It'll update these files' records
     in our production MariaDB and then removes it from Bucket-A.
   - Create a cron job that checks the DynamoDb table and **Bulk
     Load** the changes to MariaDB and then remove these files from BucketA.

Pros:
 - More resilience, as files are not updated unless they get committed to Bucket-B and Bucket-B acknowledges it and invokes Lambda-2.
 - More performant, we won't be overwhelming MariaDB with requests as much as the previous approach.
 - It's Faster/Safer than using any other CLI tool.

Cons:
 - Additional costs, of the lambda functions which will add up quickly. Costs of
   DynamoDB and the Costs of S3 storage of the duplicated files between Bucket-A
   and Bucket-B till it gets removed with our cron job.
 - The Lambda-2 will be invoked needlessly from all the non migration-related put events.

- ### Typical Script 

We can create a small script that can do the job. Combining a little bit of
*concurrency*, splitting the retrieval into chunks from
the database and performing our bulk DB updates we can greatly minimize the processing overhead on our database where we can reach good result by taking a slow but consistent approach.

The flow will be like this:

1. Read a chunk of old files from MariaDB.
2. Copying these files using AWS SDK from BucketA to BucketB.
3. Run multiple copying functions concurrently.
4. Saving the results of the copying process.
5. Update MariaDB with the results and remove the successfully copied files. 
6. Repeat.

PseudoCode:
```
// Read from Database
const LegacyFiles = DB.find({legacy: true, Limit=50})


// Functions for Copying the files
func Copy(ObjectName string) int {
    Copy the ObjectName from BucketA to BucketB

    return results of the copying process
}

// LegacyFiles
// Fire a copy operations concurrently 
for files in LegacyFiles {
 go Copy(file)
}

Db.update(list of successfully copied files)

```

Pros:
 - Straight-forward approach, easier in the process of writing and implementation.
 - Won't overwhelm MariaDB with requests.
 - Cheap no extra costs needed.

Cons:
 - Slow.


## Conclusion

If the budget is not a problem and we want to move these files as fast as
possible I'll go with option two But if the copying time isn't an issue for us I'll go
with the third option.

