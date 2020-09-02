#!/usr/bin/env python3

import sys
import calendar
import datetime
import curses
import signal

DATE_FORMAT = "%d.%m.%Y"

COURSES = {}


def course_wrap(key: str):
    """ Return courses from COURSES object or empty list on key error """

    try:
        courses = COURSES[key]
    except KeyError as e:
        courses = []

    return courses


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

    def __init__(self):
        # Start curses mode
        curses.initscr()
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
        # The window we draw our calendar
        self.window = curses.newwin(80, 120, 1, 2)
        # All those F and arrow keys
        self.window.keypad(True)

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
                self.reset_links()
                self.draw_day()
            elif c == ord('n'):
                self.reset_links()
                self.draw_week()
            elif c == ord('m'):
                self.reset_links()
                self.draw_month()
            else:
                self.handle_movement(c)

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
                f"{course.time.time}    {course.name} {course.cid}", 70)
            self.current_y += 1
            self.current_x = 15
            self.draw_string(course.time.place)
            self.current_x = 0
            self.current_y += 2

        self.window.refresh()

    def draw_week(self, init: bool = True):
        self.draw_mode = "week"
        self.window.clear()

        row_len = 20
        row_text_len = row_len - 2
        week_dates = generate_dates("week")

        # TODO: make a single lecture selectable so we can show the full info
        # TODO: show week column by column if the screen is too small
        # TODO: do we need to support weekends?

        self.reset_xy()
        self.draw_string(f"{week_dates[0]} - {week_dates[4]}")

        for i, date in enumerate(week_dates[:5], 0):
            self.current_y = 2
            self.current_x = row_len * i
            highlight = True

            # Take the full date so we can load it later
            if init:
                if len(self.draw_link_list) == 0:
                    self.draw_link_list.append([date])
                else:
                    self.draw_link_list[0].append(date)

                highlight = False

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
                self.draw_string(course.time.time, row_text_len)
                self.current_y += 1
                self.draw_string(course.name, row_text_len)
                self.current_y += 1
                self.draw_string(course.cid, row_text_len)
                self.current_y += 1
                self.draw_string(course.time.place, row_text_len)
                self.current_y += 2

        self.window.refresh()

    def draw_month(self, init: bool = True):
        self.draw_mode = "month"
        self.window.clear()

        row_len = 20
        row_text_len = row_len - 2
        month_dates = generate_dates("month")

        # TODO: show the last days of prev month and first days of next month
        #       if the first day is not monday and/or last day is not friday-sunday
        # TODO: make a single lecture selectable so we can show the full info
        # TODO: show month column by column if the screen is too small
        # TODO: do we need to support weekends?

        self.reset_xy()
        self.draw_string(
            f"{month_dates[0][0]} - {month_dates[len(month_dates) -1][0]}")

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

            self.current_x = row_len * week_day
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
                self.draw_string(course.time.time, row_text_len)
                self.current_y += 1
                self.draw_string(course.name, row_text_len)

            self.current_y -= (cousers_len * 2)

            if week_day == 4:  # Move to next week after friday
                self.current_y += (max_lines_week * 2) + 2
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
        for i in range(month_day - 1, 0, -1):
            day = current_day + datetime.timedelta(-i)
            dates.append((day.strftime(DATE_FORMAT), day.weekday()))

        # Get days after
        for i in range((month_max + 1) - month_day):
            day = current_day + datetime.timedelta(i)
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
    drawer.draw_loop()
