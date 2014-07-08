import process_feeds, time

seconds_to_sleep = 60

while True:
    print("%s --- Processing feeds" % (time.strftime("%Y/%d/%m %H:%M")))
    try:
        process_feeds.rss2tent()
    except:
        e = sys.exc_info()[0]
        print(e)
    time.sleep(seconds_to_sleep)
