#!~/virtualenv-1.10/myVE/bin/python



from threading import Thread
import time

def pr():
   integer = 9999
   while True:

      time.sleep(3)
      print str(integer)


def main():
   time.sleep(3)
   tr = Thread(target=pr)
   tr.start()
   print "Thread Started"
   count = 0
   while count < 20:
      time.sleep(1)
      count += 1
      print count

main()
