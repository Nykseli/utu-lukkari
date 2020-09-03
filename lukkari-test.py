#!/usr/bin/env python3

import sys

if sys.version_info[0] != 3 or sys.version_info[1] < 6:
    print("Python version needs to be >= 3.6")
    print("Was: {}.{}".format(sys.version_info[0], sys.version_info[1]))
    exit(1)

import unittest
import utulukkari


class LukkariTests(unittest.TestCase):
    """ The main class for test cases """

    def test_globals(self):
        """ Make sure that the global values are defined correctly in production """

        self.assertEqual(utulukkari.WIN_WIDTH, -1)
        self.assertEqual(utulukkari.WIN_HEIGHT, -1)
        self.assertEqual(utulukkari.DEBUG, False)


if __name__ == "__main__":
    unittest.main()
