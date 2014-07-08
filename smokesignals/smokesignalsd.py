import process_feeds, time

seconds_to_sleep = 60

while True:
    print("%s --- Processing feeds" % (time.strftime("%Y/%d/%m %H:%M")))
    process_feeds.rss2tent()
    time.sleep(seconds_to_sleep)
