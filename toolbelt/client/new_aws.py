import json
import os
import tempfile
import time

import boto3
import botocore.exceptions


class S3Client:
    def __init__(self, bucket: str):
        self.bucket_name = bucket

        self.s3 = boto3.client("s3")

    def read_file(self, path):
        response = self.s3.get_object(Bucket=self.bucket_name, Key=path)
        contents = response["Body"].read().decode("utf-8")
        return contents

    def upload(self, contents: str, path: str):
        self.s3.put_object(Bucket=self.bucket_name, Key=path, Body=contents)


def create_invalidation(path_list, distribution_id: str):
    client = boto3.client("cloudfront")
    distributions = client.list_distributions()
    assert distribution_id in [
        item["Id"] for item in distributions["DistributionList"]["Items"]
    ]

    items = [f"/{path}" for path in path_list]
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#CloudFront.Client.create_invalidation
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "Paths": {"Quantity": len(items), "Items": items},
            "CallerReference": str(time.time()).replace(".", ""),
        },
    )

    return response["Invalidation"]["Id"]
