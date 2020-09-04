#!/usr/bin/env python3

import sys
import calendar
import datetime
import curses
import signal

DATE_FORMAT = "%d.%m.%Y"

COURSES = {}

# datetime object for keeping track of the current date
CURRENT_DAY = datetime.datetime.now()


# Hardcoded values for testing the "responsiviness" on the smaller screen
# Should AWLAYS be -1 on production
# When set to -1 the values come from curses window
WIN_WIDTH = -1
WIN_HEIGHT = -1

# DEBUG should always be false in production
DEBUG = False


def course_wrap(key: str):
    """ Return courses from COURSES object or empty list on key error """

    try:
        courses = COURSES[key]
    except KeyError as e:
        courses = []

    return courses


def next_day(skip_weekend: bool = True):
    """ Set the CURRENT_DAY global to the next day """
    global CURRENT_DAY

    CURRENT_DAY += datetime.timedelta(1)
    week_day = CURRENT_DAY.weekday()

    if skip_weekend:
        if week_day == 5:  # Skip the Saturday
            CURRENT_DAY += datetime.timedelta(2)
        elif week_day == 6:  # Skip the Sunday
            CURRENT_DAY += datetime.timedelta(1)


def prev_day(skip_weekend: bool = True):
    """ Set the CURRENT_DAY global to the previous day """
    global CURRENT_DAY

    CURRENT_DAY -= datetime.timedelta(1)
    week_day = CURRENT_DAY.weekday()

    if skip_weekend:
        if week_day == 5:  # Skip the Saturday
            CURRENT_DAY -= datetime.timedelta(1)
        elif week_day == 6:  # Skip the Sunday
            CURRENT_DAY -= datetime.timedelta(2)


def next_week():
    """ Set the current day to the next weeks monday """
    global CURRENT_DAY

    week_day = CURRENT_DAY.weekday()
    CURRENT_DAY += datetime.timedelta(7 - week_day)


def prev_week():
    """ Set the current day to the previous weeks monday """
    global CURRENT_DAY

    week_day = CURRENT_DAY.weekday()
    CURRENT_DAY -= datetime.timedelta(week_day + 1)


def next_month():
    """ Set the current day to the next months first day """
    global CURRENT_DAY

    year = CURRENT_DAY.year
    month = CURRENT_DAY.month + 1
    if month > 12:
        month = 1
        year += 1

    CURRENT_DAY = datetime.datetime(year, month, 1)


def prev_month():
    """ Set the current day to the previous months first day """
    global CURRENT_DAY

    year = CURRENT_DAY.year
    month = CURRENT_DAY.month - 1
    if month < 1:
        month = 12
        year -= 1

    CURRENT_DAY = datetime.datetime(year, month, 1)


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

    draw_mode = None
    draw_link_x = -1
    draw_link_y = -1
    draw_link_list = []

    # Column size and amount of text in column in letters
    column_size = 20
    column_text_len = column_size - 2

    # Set to True if there is a problem with initializing the program.
    # If this is true. The draw loop should not be started
    init_error = False

    def __init__(self):
        # Start curses mode
        self.root_win = curses.initscr()
        # Line buffering disabled, Pass on everty thing to me
        curses.cbreak()
        # Don't show keypresses
        curses.noecho()
        # Hide cursor
        curses.curs_set(0)
        # Make sure that color is working
        curses.start_color()
        # Link color
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        # Set the window to be as big as possible
        if DEBUG and WIN_HEIGHT != -1 and WIN_WIDTH != -1:
            self.maxy, self.maxx = (WIN_HEIGHT, WIN_WIDTH)
        else:
            self.maxy, self.maxx = self.root_win.getmaxyx()
        # The window we draw our calendar
        self.window = curses.newwin(self.maxy, self.maxx, 1, 2)
        # Take the padding into account with maxy and maxx
        self.maxx -= 2
        self.maxy -= 1
        # All those F and arrow keys
        self.window.keypad(True)
        # Calculate the max amount of columns for responsiveness
        self.max_columns = int(self.maxx / self.column_size)
        if self.max_columns < 1 or self.maxy < 30:
            self.destroy()
            self.init_error = True
            print("Error: Screen is too small for this application")
            return

        if DEBUG:
            self.root_win.addnstr(
                f"my {self.maxy} mx {self.maxx} cols {self.max_columns}",
                self.maxx
            )
            self.root_win.refresh()

    def destroy(self):
        curses.endwin()

    def turn_highlight_on(self):
        self.window.attron(curses.color_pair(1))
        self.window.attron(curses.A_REVERSE)

    def turn_highlight_off(self):
        self.window.attroff(curses.color_pair(1))
        self.window.attroff(curses.A_REVERSE)
        pass

    def reset_xy(self):
        self.current_y = 0
        self.current_x = 0

    def reset_links(self):
        self.draw_link_x = -1
        self.draw_link_y = -1
        self.draw_link_list = []

    def handle_movement(self, c):
        list_len = len(self.draw_link_list)
        if list_len == 0:
            return

        day_str = None
        if c == ord('l') or c == curses.KEY_RIGHT:
            if self.draw_link_y == -1:
                self.draw_link_y = 0
            val = self.draw_link_x
            ylen = len(self.draw_link_list[self.draw_link_y])
            self.draw_link_x = (val + 1) % ylen
        elif c == ord('h') or c == curses.KEY_LEFT:
            if self.draw_link_y == -1:
                self.draw_link_y = 0

            ylen = len(self.draw_link_list[self.draw_link_y])
            if self.draw_link_x == -1:
                self.draw_link_x = ylen - 1
            else:
                val = self.draw_link_x
                valy = self.draw_link_y
                self.draw_link_x = (val + ylen - 1) % ylen
                # Skip empties when going to left, rest are handled after ifs
                # If every item is -1, we are going to have a bad time
                while self.draw_link_list[valy][self.draw_link_x] == -1:
                    val = self.draw_link_x
                    self.draw_link_x = (val + ylen - 1) % ylen

        elif c == ord('k') or c == curses.KEY_UP:
            if self.draw_link_x == -1:
                self.draw_link_x = 0

            if self.draw_link_y == -1:
                self.draw_link_y = list_len - 1
            else:
                val = self.draw_link_y
                self.draw_link_y = (val + list_len - 1) % list_len

            nxlen = len(self.draw_link_list[self.draw_link_y])
            if self.draw_link_x >= nxlen:
                self.draw_link_x = nxlen - 1
        elif c == ord('j') or c == curses.KEY_DOWN:
            if self.draw_link_x == -1:
                self.draw_link_x = 0
            val = self.draw_link_y
            self.draw_link_y = (val + 1) % list_len

            nxlen = len(self.draw_link_list[self.draw_link_y])
            if self.draw_link_x >= nxlen:
                self.draw_link_x = nxlen - 1
        elif c == ord('\n'):
            if self.draw_link_x != -1:
                day_str = self.draw_link_list[self.draw_link_y][self.draw_link_x]
                self.draw_mode = "day"
        else:
            # Don't do anything if there is no match
            return

        # Skip empties
        # If every item is -1, we are going to have a bad time
        ylen = len(self.draw_link_list[self.draw_link_y])
        while self.draw_link_list[self.draw_link_y][self.draw_link_x] == -1:
            val = self.draw_link_x
            self.draw_link_x = (val + 1) % ylen

        if self.draw_mode == "week":
            self.draw_week(False)
        elif self.draw_mode == "month":
            self.draw_month(False)
        elif self.draw_mode == "day":
            self.draw_day(day_str)

    def draw_loop(self):
        self.draw_day()
        while True:
            c = self.window.getch()
            if c == ord('q'):
                self.destroy()
                break
            elif c == ord('b'):
                self.draw_mode = "day"
            elif c == ord('n'):
                self.draw_mode = "week"
            elif c == ord('m'):
                self.draw_mode = "month"
            elif c == ord('p'):
                if self.draw_mode == "day":
                    next_day()
                elif self.draw_mode == "week":
                    next_week()
                elif self.draw_mode == "month":
                    next_month()
            elif c == ord('o'):
                if self.draw_mode == "day":
                    prev_day()
                elif self.draw_mode == "week":
                    prev_week()
                elif self.draw_mode == "month":
                    prev_month()
            else:
                self.handle_movement(c)
                continue

            self.reset_links()
            if self.draw_mode == "week":
                self.draw_week()
            elif self.draw_mode == "month":
                self.draw_month()
            elif self.draw_mode == "day":
                self.draw_day()

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

    def draw_day(self, day_str: str = None):
        self.draw_mode = "day"
        self.window.clear()

        if not day_str:
            day_str = generate_dates("now")[0]
        courses = course_wrap(day_str)

        self.reset_xy()
        self.draw_string(day_str)
        self.current_y = 2

        if len(courses) == 0:
            self.draw_string("No lectures today!")
            self.window.refresh()
            return

        for course in courses:
            self.draw_string(
                f"{course.time.time}    {course.name} {course.cid}", self.maxx)
            self.current_y += 1
            self.current_x = 15
            self.draw_string(course.time.place, self.maxx - self.current_x)
            self.current_x = 0
            self.current_y += 2

        self.window.refresh()

    def draw_week(self, init: bool = True):
        self.draw_mode = "week"
        self.window.clear()

        week_dates = generate_dates("week")[:5]

        # We want all 5 dates to to our draw list regradless of
        # how many columns we can draw
        if init:
            for date in week_dates:
                # Take the full date so we can load it later
                if len(self.draw_link_list) == 0:
                    self.draw_link_list.append([date])
                else:
                    self.draw_link_list[0].append(date)

        if self.max_columns < 5:
            start = self.draw_link_x
            if start == -1:
                start = 0
            else:
                start -= start % self.max_columns
            week_dates = week_dates[start:start + self.max_columns]

        # TODO: make a single lecture selectable so we can show the full info
        # TODO: do we need to support weekends?

        self.reset_xy()

        if self.maxx < 25:
            self.draw_string(
                f"{week_dates[0][:6]} - {week_dates[-1][:6]}", self.maxx)
        else:
            self.draw_string(f"{week_dates[0]} - {week_dates[-1]}", self.maxx)

        for i, date in enumerate(week_dates, 0):
            self.current_y = 2
            self.current_x = self.column_size * i
            highlight = True

            if self.draw_link_x == -1:
                highlight = False
            elif self.draw_link_list[0][self.draw_link_x] != date:
                highlight = False

            if highlight:
                self.turn_highlight_on()
            self.draw_string(f"  {date[:6]}")
            if highlight:
                self.turn_highlight_off()

            self.current_y = 4
            courses = course_wrap(date)
            for course in courses:
                self.draw_string(course.time.time, self.column_text_len)
                self.current_y += 1
                self.draw_string(course.name, self.column_text_len)
                self.current_y += 1
                self.draw_string(course.cid, self.column_text_len)
                self.current_y += 1
                self.draw_string(course.time.place, self.column_text_len)
                self.current_y += 2

        self.window.refresh()

    def draw_month(self, init: bool = True):
        self.draw_mode = "month"
        self.window.clear()

        month_dates = generate_dates("month")

        compact_column_size = int(self.maxx / 5)
        if compact_column_size >= 20:
            compact_column_size = 20
            compact_column_text_len = compact_column_size - 2
        else:
            compact_column_text_len = compact_column_size - 1

        # TODO: show the last days of prev month and first days of next month
        #       if the first day is not monday and/or last day is not friday-sunday
        # TODO: make a single lecture selectable so we can show the full info
        # TODO: show month column by column if the screen is too small
        # TODO: do we need to support weekends?

        self.reset_xy()
        self.draw_string(f"{month_dates[0][0]} - {month_dates[-1][0]}")

        self.current_y = 2
        max_lines_week = 0
        # Keep track where to put dates when initializeing draw_link_list
        draw_date_index = 0
        for _date in month_dates:
            date, week_day = _date
            if week_day == 5 or week_day == 6:  # Skip saturday and sunday
                continue
            highlight = True

            if init:
                if len(self.draw_link_list) - 1 < draw_date_index:
                    # Add empties to start if week doesn't start on monday
                    if week_day != 0:
                        self.draw_link_list.append([-1] * week_day)
                        self.draw_link_list[draw_date_index].append(date)
                    else:
                        self.draw_link_list.append([date])
                else:
                    self.draw_link_list[draw_date_index].append(date)
                highlight = False

            lx = self.draw_link_x
            ly = self.draw_link_y
            if lx == -1 or ly == -1:
                highlight = False
            elif self.draw_link_list[ly][lx] != date:
                highlight = False

            self.current_x = compact_column_size * week_day
            if highlight:
                self.turn_highlight_on()
            self.draw_string(date[:6])
            if highlight:
                self.turn_highlight_off()
            courses = course_wrap(date)
            cousers_len = len(courses)
            if cousers_len > max_lines_week:
                max_lines_week = cousers_len

            for course in courses:
                self.current_y += 1
                self.draw_string(
                    f"{course.time.time[:2]} {course.name}",
                    compact_column_text_len
                )

            self.current_y -= cousers_len

            if week_day == 4:  # Move to next week after friday
                self.current_y += max_lines_week + 2
                max_lines_week = 0
                draw_date_index += 1

        self.window.refresh()


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

    Note that month returns tuple with (date, weekday)

    TODO: date-str: courses based on date-str
    """

    dates = []
    if not keyword:
        dates.append(CURRENT_DAY.strftime(DATE_FORMAT))
    elif keyword == "today" or keyword == "now":
        dates.append(CURRENT_DAY.strftime(DATE_FORMAT))
    elif keyword == "week":
        # 0 is monday, 6 is sunday
        weekday = calendar.weekday(
            CURRENT_DAY.year, CURRENT_DAY.month, CURRENT_DAY.day)

        # Get today, and days before
        for i in range(weekday, 0, -1):
            day = CURRENT_DAY + datetime.timedelta(-i)
            dates.append(day.strftime(DATE_FORMAT))

        # Get days after
        for i in range(7 - weekday):
            day = CURRENT_DAY + datetime.timedelta(i)
            dates.append(day.strftime(DATE_FORMAT))

    elif keyword == "month":
        # Month days start from 1
        month_day = CURRENT_DAY.day
        month_max = calendar.monthrange(CURRENT_DAY.year, CURRENT_DAY.month)[1]

        # Get today, and days before
        for i in range(month_day - 1, 0, -1):
            day = CURRENT_DAY + datetime.timedelta(-i)
            dates.append((day.strftime(DATE_FORMAT), day.weekday()))

        # Get days after
        for i in range((month_max + 1) - month_day):
            day = CURRENT_DAY + datetime.timedelta(i)
            dates.append((day.strftime(DATE_FORMAT), day.weekday()))

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
    if not drawer.init_error:
        # TODO: should this be wrapped in try-expect so the window could be
        #       properly destroyed
        drawer.draw_loop()
