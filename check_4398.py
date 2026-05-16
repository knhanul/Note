path = r'e:\Pjt\Note2\qml\Main.qml'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(4393, 4405):
    line = lines[i]
    open_count = line.count('{')
    close_count = line.count('}')
    print(f'Line {i+1}: opens={open_count}, closes={close_count} | {line.rstrip()}')
