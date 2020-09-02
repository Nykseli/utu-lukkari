#!/usr/bin/env python3

import sys
import calendar
import datetime
import curses
import signal

DATE_FORMAT = "%d.%m.%Y"

COURSES = {}


class CourseTime:
    def __init__(self, day, time, place, day_name):
        self.day = day
        self.time = time
        self.place = place
        self.day_name = day_name

    def __str__(self):
        return f"{self.day_name} {self.day} {self.time} {self.place}"

    @staticmethod
    def str_to_time(string: str) -> object:
        parts = string.split()
        day_name = parts[0]
        day = parts[1]
        time = parts[2]
        place = " ".join(parts[3:])

        return CourseTime(day, time, place, day_name)


class Course:
    def __init__(self, name: str, cid: str, time: str):
        self.name = name
        self.cid = cid
        self.time = CourseTime.str_to_time(time)

    def __str__(self):
        return f"{self.name} {self.cid} {str(self.time)}"


class DateDrawer:
    """
    Ncursers wrapper that handles the drawing of the 'Lecture calendar'
    """

    # Position inside of the ncurses window (self.window)
    current_x = 0
    current_y = 0

    def __init__(self):
        # Start curses mode
        self.main_win = curses.initscr()
        # Line buffering disabled, Pass on everty thing to me
        curses.cbreak()
        # Don't show keypresses
        curses.noecho()
        # Hide cursor
        curses.curs_set(0)
        # All those F and arrow keys
        self.main_win.keypad(True)
        # The window we draw our calendar
        self.window = curses.newwin(80, 120, 1, 2)

    def destroy(self):
        curses.endwin()

    def draw_loop(self):
        self.draw_week()
        while True:
            c = self.window.getch()
            if c == ord('q'):
                self.destroy()
                break

    def draw_string(self, string: str, max_len: int = -1):
        """Draw a string to the current x, y location"""
        if max_len == -1:
            self.window.addstr(
                self.current_y, self.current_x, string)
        else:
            self.window.addnstr(
                self.current_y, self.current_x, string, max_len)

    def draw_single_lecture(self):
        pass

    def draw_day(self):

        day_str = generate_dates("now")[0]

        try:
            courses = COURSES[day_str]
        except KeyError as e:
            courses = []

        self.draw_string(day_str)
        self.current_y = 2

        if len(courses) == 0:
            self.draw_string("No lectures today!")
            self.window.refresh()
            return

        for course in courses:
            self.draw_string(
                f"{course.time.time}    {course.name} {course.cid}", 70)
            self.current_y += 1
            self.current_x = 15
            self.draw_string(course.time.place)
            self.current_x = 0
            self.current_y += 2

        self.window.refresh()

    def draw_week(self):
        row_len = 20
        row_text_len = row_len - 2
        week_dates = generate_dates("week")

        # TODO: make dates selectable so we can show the single date info
        # TODO: make a single lecture selectable so we can show the full info
        # TODO: do we need to support weekends?

        self.draw_string(f"{week_dates[0]} - {week_dates[4]}")

        for i, date in enumerate(week_dates[:5], 0):
            self.current_y = 2
            self.current_x = row_len * i
            self.draw_string(f"  {date[:6]}")
            self.current_y = 4
            try:
                courses = COURSES[date]
            except KeyError as e:
                courses = []
            for course in courses:
                self.draw_string(course.time.time, row_text_len)
                self.current_y += 1
                self.draw_string(course.name, row_text_len)
                self.current_y += 1
                self.draw_string(course.cid, row_text_len)
                self.current_y += 1
                self.draw_string(course.time.place, row_text_len)
                self.current_y += 2

        self.window.refresh()
        pass

    def draw_month(self):
        pass


def parse_lukkari_file(file_path: str):
    global COURSES

    file_lines = []
    with open(file_path) as lukkari_file:
        file_lines = lukkari_file.readlines()

    tunnus_found = False
    tunnus = None
    nimi_found = False
    nimi = None

    for line in file_lines:
        line = line.strip()

        # empty lines divides the Kurssi entries
        if len(line) == 0:
            nimi_found = False
            tunnus_found = False
            continue

        if line[0] == '#':  # skip comment lines
            continue

        # Tunnus is always the first
        if not tunnus_found:
            tunnus = line
            tunnus_found = True
            continue

        # Nimi is always the second
        if not nimi_found:
            nimi = line
            nimi_found = True
            continue

        # The rest of the lines are the course hours
        course = Course(nimi, tunnus, line)
        if not course.time.day in COURSES:
            COURSES[course.time.day] = [course]
        else:
            COURSES[course.time.day].append(course)

    # Sort the course list to make sure the early lectures are first
    for key in COURSES.keys():
        COURSES[key].sort(key=lambda course: course.time.time)


def generate_dates(keyword: str = None) -> list:
    """
    Generate dates based on keyword
    today / now / None: only todays date
    week: all dates belonging to the week we are currently living
    month: all dates belonging to the month we are currently living
    TODO: date-str: courses based on date-str
    """

    dates = []
    current_day = datetime.datetime.today()
    if not keyword:
        dates.append(current_day.strftime(DATE_FORMAT))
    elif keyword == "today" or keyword == "now":
        dates.append(current_day.strftime(DATE_FORMAT))
    elif keyword == "week":
        # 0 is monday, 6 is sunday
        weekday = calendar.weekday(
            current_day.year, current_day.month, current_day.day)

        # Get today, and days before
        for i in range(weekday, 0, -1):
            day = current_day + datetime.timedelta(-i)
            dates.append(day.strftime(DATE_FORMAT))

        # Get days after
        for i in range(7 - weekday):
            day = current_day + datetime.timedelta(i)
            dates.append(day.strftime(DATE_FORMAT))

    elif keyword == "month":
        # Month days start from 1
        month_day = current_day.day
        month_max = calendar.monthrange(current_day.year, current_day.month)[1]

        # Get today, and days before
        for i in range(month_day, 1, -1):
            day = current_day + datetime.timedelta(-i)
            dates.append(day.strftime(DATE_FORMAT))

        # Get days after
        for i in range((month_max + 1) - month_day):
            day = current_day + datetime.timedelta(i)
            dates.append(day.strftime(DATE_FORMAT))

    else:
        print(f"Invalid date keyword: {keyword}")

    return dates


def main():
    target_days = []
    if len(sys.argv) == 2:
        target_days = generate_dates(sys.argv[1])
    else:
        target_days = generate_dates()
    kurssit = parse_lukkari_file("lukkari.txt")
    for target_day in target_days:
        for kurssi in kurssit:
            for tunti in kurssi.tunnit:
                if target_day == tunti.day:
                    print(f"Nimi: {kurssi.nimi} ({kurssi.tunnus})")
                    print(f"Aika: {tunti}\n")


def interrupt_handler(signal_received, frame):
    """
    Destroy drawer window so the terminal doesn't get all wonky
    """

    drawer.destroy()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_handler)
    parse_lukkari_file("lukkari.txt")

    drawer = DateDrawer()
    drawer.draw_loop()

    # week_dates = generate_dates("week")
    # for i, date in enumerate(week_dates, 1):
    #     current_x = 30 * i
    #     print(f"        {date[:6]}")
