from datetime import datetime
from DB.models import Time


def getDuration(duration, interval="default"):

    # Returns a duration as specified by variable interval
    # Functions, except totalDuration, returns [quotient, remainder]

    duration_in_s = duration.total_seconds()

    def years():
        return divmod(duration_in_s, 31536000)  # Seconds in a year=31536000.

    def days(seconds=None):
        # Seconds in a day = 86400
        return divmod(seconds if seconds != None else duration_in_s, 86400)

    def hours(seconds=None):
        # Seconds in an hour = 3600
        return divmod(seconds if seconds != None else duration_in_s, 3600)

    def minutes(seconds=None):
        # Seconds in a minute = 60
        return divmod(seconds if seconds != None else duration_in_s, 60)

    def seconds(seconds=None):
        if seconds != None:
            return divmod(seconds, 1)
        return duration_in_s

    def totalDuration():
        y = years()
        d = days(y[1])  # Use remainder to calculate next variable
        h = hours(d[1])
        m = minutes(h[1])
        s = seconds(m[1])

        return Time(hours=int(h[0]), minutes=int(m[0]), seconds=int(s[0]))

    return {
        'hours': int(hours()[0]),
        'minutes': int(minutes()[0]),
        'seconds': int(seconds()),
        'default': totalDuration()
    }[interval]
