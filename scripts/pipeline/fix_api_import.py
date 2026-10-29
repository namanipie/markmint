def run():
    path = "src/lib/api.ts"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    old_imp = 'import canonicalCatalog from "@/data/canonical_curriculum.json";'
    new_imp = 'import canonicalCatalog from "./canonical_curriculum.json";'

    if old_imp in c:
        c = c.replace(old_imp, new_imp)
        with open(path, "w", encoding="utf-8") as f:
            f.write(c)
        print("Successfully updated src/lib/api.ts to sibling import!")
    else:
        print("Target import not found, searching...")
        import re
        c = re.sub(
            r'import\s+canonicalCatalog\s+from\s+["\']@/data/canonical_curriculum\.json["\'];',
            'import canonicalCatalog from "./canonical_curriculum.json";',
            c
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(c)
        print("Replaced via regex!")

if __name__ == "__main__":
    run()
