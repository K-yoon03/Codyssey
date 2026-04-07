from datetime import datetime
import time
import json
import random


class DummySensor:
    def __init__(self):  # 생성자 : Python에서는 필드 선언과 초기화를 동시에 진행
        self.env_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0
        }

    def set_env(self):
        # 랜덤 값을 통해 센서 데이터 생성 (실제 센서값을 대체하는 더미 데이터)
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)  # 실수값이라 uniform 사용
        self.env_values['mars_base_external_temperature'] = round(random.uniform(-80, 0), 2)  # 화성 외부 환경 반영
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(40, 60), 2)  # 습도 범위 설정
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(300, 800), 2)  # 광량
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.08), 4)  # CO2 농도
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(19, 21), 2)  # 산소 농도 (지구 기준)

    def get_env(self):  # getter Method : Java와 유사하지만 self를 명시적으로 전달
        self.set_env()  # 값을 요청할 때마다 최신 값으로 갱신

        now = datetime.now()  # 현재 시간 가져오기
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')  # 문자열 형태로 변환

        # dict의 value만 추출하여 문자열 리스트로 변환
        values = [str(value) for value in self.env_values.values()]

        # 로그 한 줄 생성 (timestamp + 센서값)
        log_line = f'{timestamp}, ' + ', '.join(values) + '\n'

        # 파일에 로그 저장 (append 모드)
        with open('mars_log.txt', 'a') as file:
            file.write(log_line)

        return self.env_values  # Python은 self를 통해 객체 데이터를 반환 (Java와 차이점 존재)


class MissionComputer:
    def __init__(self):  # 생성자 : 미션 컴퓨터 초기 설정
        self.env_values = {
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0
        }

        self.ds = DummySensor()  # DummySensor 객체 생성 (센서 역할)

        self.history = []  # 5분 평균 계산을 위한 데이터 저장 리스트
        self.start_time = time.time()  # 시작 시간 기록

    def get_sensor_data(self):
        print('Press Ctrl + C to stop...')  # 사용자에게 종료 방법 안내

        try:
            while True:  # 무한 반복 (실시간 센서 모니터링)
                # 1. 센서 데이터 가져오기
                data = self.ds.get_env()

                # 2. env_values에 최신 데이터 반영
                self.env_values.update(data)

                # 3. JSON 형태로 출력 (가독성을 위해 indent 사용)
                print(json.dumps(self.env_values, indent=4))

                # 평균 계산을 위해 현재 데이터 복사하여 저장 (참조 방지)
                self.history.append(self.env_values.copy())

                # 5분(300초) 경과 시 평균 출력
                if time.time() - self.start_time >= 300:
                    self.print_average()
                    self.history.clear()  # 기존 데이터 초기화
                    self.start_time = time.time()  # 시간 재설정

                time.sleep(5)  # 5초 대기 (주기적 실행)

        except KeyboardInterrupt:
            # Ctrl + C 입력 시 예외 발생 → 프로그램 종료 처리
            print('System stopped....')

    def print_average(self):
        if not self.history:  # 데이터가 없을 경우 처리
            return

        avg_values = {}

        # 각 key에 대해 평균 계산
        for key in self.history[0]:
            total = sum(item[key] for item in self.history)
            avg_values[key] = round(total / len(self.history), 4)

        print('\n===== 5 Minute Average =====')
        print(json.dumps(avg_values, indent=4))  # 평균값도 JSON 형태로 출력
        print('============================\n')


# 실행 영역 : Java의 main 메소드와 유사한 역할
if __name__ == '__main__':
    RunComputer = MissionComputer()  # 객체 생성
    RunComputer.get_sensor_data()  # 메소드 실행 (무한 루프 시작)