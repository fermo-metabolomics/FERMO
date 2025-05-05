import os
import shutil
import time
from datetime import datetime, timedelta


def delete_old_directories(target_dir, age_limit):
    """Remove directories older than n days

    Arguments:
        target_dir: the target directory in which dirs should be removed
        age_limit: the age limit of directories in days
    """
    now = datetime.now()
    age_limit_delta = timedelta(days=age_limit)

    for dirname in os.listdir(target_dir):
        dirpath = os.path.join(target_dir, dirname)
        if os.path.isdir(dirpath) and not dirname.startswith("example"):
            dir_mod_time = datetime.fromtimestamp(os.path.getmtime(dirpath))
            if now - dir_mod_time > age_limit_delta:
                shutil.rmtree(dirpath, ignore_errors=True)


def main():
    """Runs infinitive loop and executes cleanup every 24h"""
    while True:
        delete_old_directories("./fermo_gui/upload", 30)
        time.sleep(86400)


if __name__ == "__main__":
    main()
