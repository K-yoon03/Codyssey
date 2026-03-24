import csv
import traceback

def main():
    inventory_list=[]
    header = []

    try:
        with open('MArs_base_Inventory_List.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader) # 해더 제외
            for data in reader:
                inventory_list.append(data)
        print('============[Original Data]============')
        for data in inventory_list:
            print(data)
        
    except Exception as e:
        print('파일을 찾을 수 없습니다.')
        traceback.print_exc()
    
    def get_flammability(item):
        try:
            return float(item[1])
        except ValueError:
            return 0.0 # 'Various' 같은 건 그냥 0으로 취급해서 뒤로 보냄
    
    inventory_list.sort(key=get_flammability, reverse=True)
    flammableList = []
    print('============[Flammable List]============')
    for list in inventory_list:
        try:
            if float(list[1]) >= 0.7:
                print(list)
                flammableList.append(list)
        except ValueError:
            continue #Value Error시 계속 진행
    
    try:
        with open('Mars_base_Inventory_danger.csv', 'w') as f :
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(flammableList)
        print('[Success]Mars_base_Inventory_danger.csv is saved')
    except Exception as e:
        traceback.print_exc()

    try:
        with open('Mars_Base_Inventory_List.bin', 'wb') as f:
            for item in inventory_list:
                row_str = ','.join(item) + '\n'
                f.write(row_str.encode('utf-8'))
        
        print('\n==========[Read Binary File]===========')
        with open('Mars_Base_Inventory_List.bin', 'rb') as f:
            print(f.read().decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    main()