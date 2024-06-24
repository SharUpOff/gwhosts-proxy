from sys import stdin

from gwhosts.dns import parse

if __name__ == "__main__":
    print(parse(stdin.buffer.read()))
