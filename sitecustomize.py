import os
import sys


def _add_repo_paths() -> None:
    repo_root = os.path.dirname(os.path.abspath(__file__))
    apps = os.path.join(repo_root, "apps")
    packages = os.path.join(repo_root, "packages")

    # Prepend so local modules win over installed packages
    if apps not in sys.path:
        sys.path.insert(0, apps)
    if packages not in sys.path:
        sys.path.insert(0, packages)


_add_repo_paths()
