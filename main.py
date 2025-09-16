#!/usr/bin/env python3

import sys

from protocol_adapter import AdapterAdmin

if __name__ == '__main__':
    admin = AdapterAdmin()
    admin.run(sys.argv[1:], wait=True)
