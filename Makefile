generate:
	bash _helperScripts/generateObjects.sh

upload:
	s3cmd sync Buckets/oldBucket/image/ s3://oldbuckets1/image/
clean:
	rm -rf Buckets/oldBucket/image/* && s3cmd rm s3://oldbuckets1/image/ --recursive
cleans:
	s3cmd rm s3://newbuckets2/ --recursive --force
populate:
	python3 _helperScripts/populatedb.py
