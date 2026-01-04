import sys
import os

# Ensure the current directory is in the path so we can import the package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from proxihud.main import main

if __name__ == "__main__":
    main()