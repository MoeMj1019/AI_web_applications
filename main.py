# regulate the whole process of the program

# TODO:
#   - improve the searching process ?

# IDEAS:
#   - let user provide a list of urls / domains / topics to for the next run of the crawler

from WebSearchEngine.index import WebIndex
from argparse import ArgumentParser

def get_args():
    parser = ArgumentParser()
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()