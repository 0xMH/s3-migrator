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

If you wanna know more about the internals and the design decisions and read
more about the architecture and your alternative solutions for Moving S3Objects
while keeping your production database in sync with the changes, Please Have
a look at our [Design Document](https://github.com/0xMH/s3-migrator/blob/main/DesignDoc.md)

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

## Features

- S3-migrator moves files concurrently, So it's fast.
- S3-migrator updates your database and change objects paths.
- S3-migrator assumes that database is the single source of truth so It can 
  resume work from where it was stopped.
- No dependencies — There's no usage of external sources (i.e. lambdas,
  DynamoDB) to keep track of the files migrations; we only rely on our script
  and database which reduces the cost of the migration. 
- S3-migrator implements exponential backoffs so it's always trying to handle
  problems that arises due of network delays and rate-limiting.
- S3-migrator is fail-safe and idempotent script, You can run it multiple times
  without expecting any problems.

## Requirements
* [Python 3.x](https://www.python.org/downloads/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) (recommended) 

## Installation
There are multiple ways to install and run S3-migrator.

- You can use it as your typical python tool by installing its dependencies
   the run it using `python s3-migrator`

    Steps:
    First, make sure you have [Python 3.x](https://www.python.org/downloads/), [pip](https://pip.pypa.io/en/stable/installing/), and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed on your machine.

    Run the following in your command prompt to install:
    1. `git clone https://github.com/0xMH/s3-migrator.git`
    2. `cd s3-migrator`
    3. `pip install -r requirements.txt`

- Run it as container using Docker:

    ```
    docker run --name s3-migrator \
    -e bucket_from="" \
    -e bucket_to="" \
    -e aws_access_key_id="" \
    -e aws_secret_access_key="" \
    -e DBUser="" \
    -e DBPassword="" \
    -e DBHost="" \
    -e DBPort="" \
    -e DATABASE="" oxmh/s3-migrator:latest
    ```

- Run it on  Kubernetes using Helm chart
    
    Check the README on helm-s3-migrator 

## Usage
Currently S3-migrator needs these env vars in order to work:

- `bucket_from=""`
- `bucket_to=""`
- `aws_access_key_id=""`
- `aws_secret_access_key=""`
- `DBUser=""`
- `DBPassword=""`
- `DBHost=""`
- `DATABASE=""`
- `DBPort=""`

You can either specify these env vars in `.env` file or export it to your shell
environment. S3-migrator isn't configurable from the CLI yet (This is on my TODO
tho) So it defaults to working on `buckets` table and `bucket_name` & `id` column.

Here's a statement that create both the table and column so you can try it on
your `MariaDB`.

```
create table buckets
(
	bucket_name char(50) null,
	id int auto_increment,
	constraint buckets_pk
		primary key (id)
);

```

Also currently it defaults to moving objects under `/image/*` on one bucket to `/avatar`
on another. 

## TODO:

- [ ] Optimizing pagination query with Seek method because offset method become
      slow and painful once the OFFSET has a high value
- [ ] Use Bulk load approach to load the changes to datbase, Maybe use either
      Load Data Infile or bulk insert Statement.
- [ ] Make it configurable and Add CLI arguments 
- [ ] Improve Helm by adding Kubernetes secrets and read env vars from it

## Contributing

Feel free to contribute by making a pull request.
