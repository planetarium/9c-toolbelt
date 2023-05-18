import json
import os
from toolbelt.constants import DATA_DIR


def update_latest(version: int, commit_hash: str):
    # 주어진 JSON 파일의 경로
    json_file_path = os.path.abspath(os.path.join(DATA_DIR, "latest.json"))

    # 파일 크기 가져오기
    new_file_size = os.path.getsize(file_path)

    # JSON 파일 열기
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)

    # 정보 수정
    data["version"] = version

    # files의 path 앞에 version 변경
    for file_info in data["files"]:
        file_info["path"] = f"{version}/{file_info['path']}"

    # size 수정
    for file_info in data["files"]:
        file_info["size"] = new_file_size

    # commit-hash 수정
    data["commit-hash"] = commit_hash
    data["timestamp"] = datetime.utcnow().strftime(timestamp_format)

current_timestamp = 


    # timestamp 자동으로 추가됨

    # 수정된 JSON 파일 저장
    with open(json_file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)


def create_version_json():
    pass
