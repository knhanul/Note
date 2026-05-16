with open('qml/Main.qml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(4395, 4405):
    line = lines[i]
    print(f'Line {i+1}: opens={line.count("{")}, closes={line.count("}")} | {line.rstrip()}')
