#!/bin/bash
for i in {0..50}
do
    name=$(cat /dev/urandom | env LC_CTYPE=C tr -cd 'a-f0-9' | head -c 5)
    touch "Buckets/oldBucket/image/${name}.png"
done

