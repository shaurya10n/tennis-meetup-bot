from pathlib import Path

def print_directory_structure(path, prefix=""):
    path = Path(path)
    for item in sorted(path.iterdir()):
        if item.name != '__pycache__':
            print(f"{prefix}├── {item.name}")
            if item.is_dir() :
                print_directory_structure(item, prefix + "│   ")

# Usage

if __name__ == "__main__":
    print_directory_structure("../src/")
