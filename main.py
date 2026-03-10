import traceback

print('Hello Mars')

try:
    filename = 'mission_computer_main.log'
    outputFilename = "log_analysis.md"
    f=open(filename, 'r')
    o=open(outputFilename, 'w')

    for i in f.readlines():
        print(i)
        
except Exception as e:
    print('오류가 발생했습니다.')
    traceback.print_exc()
else:
    print(f'{filename}이 정상적으로 출력되었습니다.')