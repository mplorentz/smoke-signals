import time, sys
import smokesignals.process_feeds as process_feeds

seconds_to_sleep = 60

while True:
    print("%s --- Processing feeds" % (time.strftime("%Y/%d/%m %H:%M")))
    try:
        process_feeds.rss2tent()
    except:
        type, message, trace = sys.exc_info()[0]
        print("%s" % (message))
    time.sleep(seconds_to_sleep)
