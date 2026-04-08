from icalendar import Calendar


def create_calendar(method):
    cal = Calendar()
    cal.add("prodid", "-//JavaZone Calendar Manager//javazone.ibidem.no//")
    cal.add("version", "2.0")
    cal.add("method", method)
    return cal
