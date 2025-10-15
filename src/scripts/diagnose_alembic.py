import os
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    print("CWD=", os.getcwd())

    cfg_path = os.path.join("src", "alembic.ini")
    print("cfg_path=", cfg_path, "exists=", os.path.exists(cfg_path))

    try:
        cfg = Config(cfg_path)
    except Exception as e:
        print("ConfigLoadError:", type(e).__name__, str(e))
        return 2

    print("config_file_name=", cfg.config_file_name)

    try:
        sl = cfg.get_main_option("script_location")
        print("script_location=", repr(sl))
    except Exception as e:
        print("GetOptionError:", type(e).__name__, str(e))
        return 3

    try:
        sd = ScriptDirectory.from_config(cfg)
        print("script_directory=", sd.dir)
        versions_dir = os.path.join(sd.dir, "versions")
        print("versions_dir=", versions_dir, "exists=", os.path.isdir(versions_dir))
    except Exception as e:
        import traceback

        print("ScriptDirectoryError:", type(e).__name__, str(e))
        traceback.print_exc()
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())