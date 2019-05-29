import argparse

from app import db


def init_db():
    db.init_db()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    args = parser.parse_args()
    if args.command == 'init_db':
        init_db()
    else:
        raise ValueError(f"Command '{args.command} not found")
