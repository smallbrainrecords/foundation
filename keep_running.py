while True:
    import os
    import time
    print 'Netstat'
    output = os.popen('cd / && netstat -lnt | grep 8000').read()
    if output == '':
        print 'Sleeping 5 seconds'
        time.sleep(5)

        os.system(' cd /home/tim/ && cd /home/tim/core/ && python /home/tim/core/manage.py runserver 0.0.0.0:8000')
    else:
        print 'Sleeping 1 second'
        time.sleep(1)
