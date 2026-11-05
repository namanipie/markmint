import os

print("=== data/downloads/cycle_tests ===")
for root, dirs, files in os.walk('data/downloads/cycle_tests'):
    if files:
        print(f"{root}:")
        for f in files:
            print(f"   {f}")

print("\n=== data/downloads/more_cycle_tests ===")
for root, dirs, files in os.walk('data/downloads/more_cycle_tests'):
    if files:
        print(f"{root}:")
        for f in files:
            print(f"   {f}")
