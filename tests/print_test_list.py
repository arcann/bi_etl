import unittest


def print_suite(suite):
    if hasattr(suite, '__iter__'):
        for x in suite:
            print_suite(x)
    else:
        if hasattr(suite, 'TEST_COMPONENT'):
            print(f"{suite.TEST_COMPONENT} {suite}")
        else:
            print(f"{repr(suite)} {suite}")


def main():
    print_suite(unittest.defaultTestLoader.discover('.'))


if __name__ == '__main__':
    main()
