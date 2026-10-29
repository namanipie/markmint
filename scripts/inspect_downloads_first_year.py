import os

print("=== Subdirectories in 'data/1 Year' ===")
for item in sorted(os.listdir("data/1 Year")):
    p = os.path.join("data/1 Year", item)
    if os.path.isdir(p):
        files = []
        for root, _, fs in os.walk(p):
            files.extend([os.path.join(root, f) for f in fs])
        print(f"Dir: {item:35s} | {len(files):3d} files")
    else:
        print(f"File: {item}")
