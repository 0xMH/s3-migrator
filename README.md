# s3-migrator

S3-migrator is a tool to facilitate migration of the objects between different
buckets and paths on AWS S3 and also updating the state of these objects on
MySQL Database.

## What makes it different from other S3 tools out there?

S3-migrator isn't the fastest tool out there to use to copy your objects
between different buckets, Although it's pretty fast and it can handle that seamlessly if
you used it for that use case, But S3-migrator was build with the intent of
**moving** several-millions of S3 objects between buckets or within the same bucket on different paths while
keeping the production Database up-to-date with the changes done and remove old
objects when it makes sure that it's both moved and updated on the database,
hence reduce costs by preventing objects duplication.

## How it compares to other S3tools?

If you decided to use s3-migrator for copying your objects without updating
your database Here's what you should expect from s3-migraor.

| tools       | Speed while copying 1k objects between S3Buckets |
|-------------|--------------------------------------------------|
| s3cmd       | 18.60 mins                                       |
| awscli      | 44.32 sec                                        |
| s3-migrator | 9.44 sec                                         |

All tests were done on my personal MacBook with the same connection. So
while copying I found that s3-migrator is much, much faster than some of the
other alternatives. 

## Feature

- S3-migrator move files concurrently, So it's fast.
- S3-migrator updates your database and change objects paths.
- S3-migrator assumes that database is the single source of truth so It can 
  resume work from where it was stopped.
- Cut costs of the migration short due to it's removing old objects after it's
  copying process is done.
- S3-migrator implement exponential backoffs so it's always trying to handle
  problems that arises due of network delays and rate-limiting.

## Requirements
* [Python 3.x](https://www.python.org/downloads/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) (recommended) 

## Installation
First, make sure you have [Python 3.x](https://www.python.org/downloads/), [pip](https://pip.pypa.io/en/stable/installing/), and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed on your machine.

Run the following in your command prompt to install:
1. `git clone https://github.com/0xMH/s3-migrator.git`
2. `cd s3-migrator`
3. `pip install -r requirements.txt`

## TODO:

- [ ] Optimizing pagination query with Seek method because offset method become
      slow and painful once the OFFSET has a high value
- [ ] Use Bulk load approach to load the changes to datbase, Maybe use either
      Load Data Infile or bulk insert Statement.
- [ ] Make it configurable and Add CLI arguments 
