import os
import shutil
import tarfile
import zipfile

from py7zr import SevenZipFile
from zipfile import ZIP_DEFLATED


def extract(dir: str, binary_path: str, use7z: bool = True) -> str:
    file_name = os.path.basename(binary_path)
    os_name, extension = file_name.split(".", 1)
    dst_path = os.path.join(dir, os_name)

    if extension == "tar.gz":
        with tarfile.open(binary_path) as zip:
            zip.extractall(dst_path)
    else:
        if use7z:
            with SevenZipFile(binary_path, mode="r") as archive:
                archive.extractall(dst_path)
        else:
            with zipfile.ZipFile(binary_path, mode="r") as archive:
                archive.extractall(path=dst_path)

    os.remove(binary_path)
    return dst_path


def extract_zipped_artifact(dir: str, file_name: str) -> str:
    os_name, extension = file_name.split(".", 1)
    path = os.path.join(dir, file_name)
    dst_path = os.path.join(dir, os_name)
    with zipfile.ZipFile(path, mode="r") as archive:
        archive.extractall(path=dst_path)
    if os_name == "Windows":
        result_file = f"{os_name}.zip"
    else:
        result_file = f"{os_name}.tar.gz"
    result_path = os.path.join(os.path.dirname(dst_path), result_file)
    os.remove(path)
    os.rename(
        os.path.join(dst_path, result_file),
        result_path
    )
    return result_path


def compress(dir: str, target_dir: str, result_path: str, use7z: bool = True) -> str:
    file_name = os.path.basename(result_path)
    os_name, extension = file_name.split(".", 1)

    if extension == "tar.gz":
        with tarfile.open(result_path, "w:gz") as zip:
            for arcname in os.listdir(target_dir):
                name = os.path.join(dir, os_name, arcname)
                zip.add(name, arcname=arcname)
    else:
        if use7z:
            with SevenZipFile(result_path, mode="w") as archive:
                for p, _, files in os.walk(target_dir):
                    for f in files:
                        filename = os.path.join(p, f)
                        archive.write(
                            file=filename,
                            arcname=filename.removeprefix(target_dir),
                        )
        else:
            with zipfile.ZipFile(result_path, mode="w", compression=ZIP_DEFLATED) as archive:
                for p, _, files in os.walk(target_dir):
                    for f in files:
                        filename = os.path.join(p, f)
                        archive.write(
                            filename=filename,
                            arcname=filename.removeprefix(target_dir),
                        )
    shutil.rmtree(target_dir)
    return result_path
