import os
import shutil

DIR_PREFIX = 'base/'

# TODO: переместить это в TimeActivity


def check_and_create_path(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def clear_base(base_directory=DIR_PREFIX):
    shutil.rmtree(base_directory, ignore_errors=True)
