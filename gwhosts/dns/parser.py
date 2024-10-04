from sys import stdin

from . import parse

if __name__ == "__main__":
    print(parse(stdin.buffer.read()))
