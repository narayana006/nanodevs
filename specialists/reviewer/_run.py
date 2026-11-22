import sys
sys.path.insert(0, sys.argv[1])
sys.path.append("/w")
import _rt
_rt.run_all("test_hidden")
