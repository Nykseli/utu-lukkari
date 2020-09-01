#!/usr/bin/env python3

import sys
import calendar
import datetime

DATE_FORMAT = "%d.%m.%Y"


class KurssiTunti:
    def __init__(self, day, time, place, day_name):
        self.day = day
        self.time = time
        self.place = place
        self.day_name = day_name

    def __str__(self):
        return f"{self.day_name} {self.day} {self.time} {self.place}"

    @staticmethod
    def str_to_tunti(string: str) -> object:
        parts = string.split()
        day_name = parts[0]
        day = parts[1]
        time = parts[2]
        place = " ".join(parts[3:])

        return KurssiTunti(day, time, place, day_name)


class Kurssi:
    def __init__(self):
        self.nimi = ""
        self.tunnus = ""
        self.tunnit = []

    def add_nimi(self, nimi: str):
        self.nimi = nimi

    def add_tunnus(self, tunnus: str):
        self.tunnus = tunnus

    def add_tunti(self, tunti: str):
        kurssi_tunti = KurssiTunti.str_to_tunti(tunti)
        self.tunnit.append(kurssi_tunti)


def parse_lukkari_file(file_path: str) -> list:
    kurssit = []

    file_lines = []
    with open(file_path) as lukkari_file:
        file_lines = lukkari_file.readlines()

    tunnus_found = False
    nimi_found = False
    kurssi = Kurssi()

    for line in file_lines:
        line = line.strip()

        # empty lines divides the Kurssi entries
        if len(line) == 0:
            nimi_found = False
            tunnus_found = False
            if kurssi.nimi:
                kurssit.append(kurssi)
            kurssi = Kurssi()
            continue

        if line[0] == '#':  # skip comment lines
            continue

        # Tunnus is always the first
        if not tunnus_found:
            kurssi.add_tunnus(line)
            tunnus_found = True
            continue

        # Nimi is always the second
        if not nimi_found:
            kurssi.add_nimi(line)
            nimi_found = True
            continue

        # The rest of the lines are the course hours
        kurssi.add_tunti(line)

    # After reading lines make sure that the last entry is added
    # if the file doesn't end with a empty line
    if kurssi.nimi and kurssi.tunnus:
        kurssit.append(kurssi)

    return kurssit


def generate_dates(keyword: str = None) -> list:
    """
    Generate dates based on keyword
    today / now / None: only todays date
    week: all dates belonging to the week we are currently living
    month: all dates belonging to the month we are currently living
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


if __name__ == '__main__':
    main()
