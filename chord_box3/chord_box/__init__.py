from pathlib import Path
import sys
from tendo import singleton


try:
    single_instance = singleton.SingleInstance()
except singleton.SingleInstanceException:
    Path('display').write_bytes(b'')
    sys.exit(2)
Path('display').unlink(True)
