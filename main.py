import traceback

print('Hello Mars')

try:
    filename = 'mission_computer_main.log'
    outputFilename = "log_analysis.md"

    f=open(filename, 'r')
    o=open(outputFilename, 'w')

    abnormal = []

    line = f.readlines()

    for i in reversed(line): # 역순으로 나열
        print(i)

    for i in line[1:]:
        data = i.strip().split(',')
        time = data[0]
        eventName = data[1]
        message = data[2]

        if 'unstable'in message or 'explosion' in message:
            abnormal.append((time, message))
    
    print(abnormal)
    o.write('# Analyzing Log result\n')
    o.write('## Abnormal Logs\n')
    for a in abnormal:
        o.write(f' - {a[0]} : {a[1]}\n')
    f.close()
    o.close()

except Exception as e:
    print('오류가 발생했습니다.')
    traceback.print_exc()
else:
    print(f'{filename}이 정상적으로 출력되었습니다.')