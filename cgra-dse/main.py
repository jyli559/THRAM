import os
import sys
from dse import thram

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cgraflow"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hebo"))

def main():
    thram(1)

if __name__ == "__main__":
    main()