import time, sys
sys.path.insert(0, ".scratch")
from lockguard import acquire_or_exit
acquire_or_exit("dup_test")
print("running alone, pid ok")
time.sleep(4)
print("finished")
