from typing import List
import json
import hashlib
from pathlib import Path
import os
from boto3 import client


def download_dir(prefix: str, local: str, bucket: str, s3_client: client):
    """
    params:
    - prefix: pattern to match in s3
    - local: local path to folder in which to place files
    - bucket: s3 bucket with target contents
    - s3_client: initialized s3 client object
    """
    keys = []
    dirs = []
    next_token = ""
    base_kwargs = {
        "Bucket": bucket,
        "Prefix": prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != "":
            kwargs.update({"ContinuationToken": next_token})
        results = s3_client.list_objects_v2(**kwargs)
        contents = results.get("Contents")
        for i in contents:
            k = i.get("Key")
            if k[-1] != "/":
                keys.append(k)
            else:
                dirs.append(k)
        next_token = results.get("NextContinuationToken")
    for d in dirs:
        dest_pathname = os.path.join(local, d)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
    for k in keys:
        dest_pathname = os.path.join(local, k)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        s3_client.download_file(bucket, k, dest_pathname)


def process_file(path: Path):
    def add_id(lst_dct: List[dict]):
        for dct in lst_dct:
            dct["id"] = hashlib.md5(str(dct).encode("utf-8")).hexdigest()
            if isinstance(dct["text"], list):
                dct["text"] = "\n\n".join(dct["text"])
        return lst_dct

    try:
        lst_dct = [json.loads(line) for line in open(path, "r").read().split("\n") if line]
        lst_dct = add_id(lst_dct)
        # path.rename(path.with_suffix(".jl"))
        with open(path, "w") as jsonl_file:
            for entry in lst_dct:
                json.dump(entry, jsonl_file)
                jsonl_file.write("\n")
    except TypeError as e:
        print(f"failed for {str(path)} because of: {e}, which might be an already processed file")
