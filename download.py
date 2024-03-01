import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    required_packages = [
        'cloudscraper',
        'concurrent',
        'requests'
    ]

    for package in required_packages:
        install(package)

if __name__ == "__main__":
    main()