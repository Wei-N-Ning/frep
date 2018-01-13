
import os


def filePath(fileName):
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), fileName
        )
    )
