with open('src/components/layout/footer.tsx', 'rb') as f:
    data = f.read()
data = data.replace(b'className="flex items-center gap-5', b'className="flex flex-wrap items-center gap-x-5 gap-y-2')
with open('src/components/layout/footer.tsx', 'wb') as f:
    f.write(data)
print('Updated footer.tsx successfully')

with open('src/components/layout/navbar.tsx', 'rb') as f:
    data = f.read()
data = data.replace(
    b'className="absolute right-1 sm:right-2 top-1/2 -translate-y-1/2"',
    b'className="hidden sm:block absolute right-2 top-1/2 -translate-y-1/2"'
)
with open('src/components/layout/navbar.tsx', 'wb') as f:
    f.write(data)
print('Updated navbar.tsx successfully')
