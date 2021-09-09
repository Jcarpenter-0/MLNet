import sys
import subprocess

# Generate some blobs

bytes = int(sys.argv[1])

subprocess.check_call("dd if=/dev/zero of={}.dat  bs={}  count=1".format(bytes, bytes), shell=True)

