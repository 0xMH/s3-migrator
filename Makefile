generate:
	bash _helperScripts/generateObjects.sh

upload:
	s3cmd sync Buckets/oldBucket/image/ s3://oldbuckets1/image/
clean:
	rm Buckets/oldBucket/image/* && s3cmd rm s3://oldbuckets1/image/ --recursive
