from datetime import datetime
import time
import json
import random
import platform
import os


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
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(-80, 0), 2)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(40, 60), 2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(300, 800), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.08), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(19, 21), 2)

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

        return self.env_values  # Python은 self를 통해 객체 데이터를 반환


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
        self.info_filters = self._load_settings('info_fields')
        self.load_filters = self._load_settings('load_fields')



    def _load_settings(self, section):
        try:
            with open('setting.txt', 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()

            in_section = False
            fields = []

            for line in lines:
                stripped = line.strip()
                if stripped == f'[{section}]':
                    in_section = True
                    continue
                if stripped.startswith('[') and stripped.endswith(']'):
                    if in_section:
                        break  # 다음 섹션 시작 → 현재 섹션 종료
                    continue
                if in_section and stripped:
                    fields.append(stripped)

            return fields if fields else None

        except FileNotFoundError:
            return None  # setting.txt 없으면 전체 출력

    def _apply_filter(self, data, filters):
        """filters 목록이 있으면 해당 키만 추출하여 반환한다."""
        if not filters:
            return data
        return {key: value for key, value in data.items() if key in filters}

    def get_sensor_data(self):
        print('Press Ctrl + C to stop...')  # 사용자에게 종료 방법 안내

        try:
            while True:  # 무한 반복 (실시간 센서 모니터링)
                data = self.ds.get_env()
                self.env_values.update(data)

                print(json.dumps(self.env_values, indent=4))

                self.history.append(self.env_values.copy())

                # 5분(300초) 경과 시 평균 출력
                if time.time() - self.start_time >= 300:
                    self.print_average()
                    self.history.clear()
                    self.start_time = time.time()

                time.sleep(5)

        except KeyboardInterrupt:
            print('System stopped....')

    def print_average(self):
        if not self.history:
            return

        avg_values = {}

        for key in self.history[0]:
            total = sum(item[key] for item in self.history)
            avg_values[key] = round(total / len(self.history), 4)

        print('\n===== 5 Minute Average =====')
        print(json.dumps(avg_values, indent=4))
        print('============================\n')

    def get_mission_computer_info(self):

        try:
            system_info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'cpu_type': platform.processor() or platform.machine(),
                'cpu_cores': os.cpu_count(),
                'memory_total': '16 GB'  # 미션 컴퓨터 사양 고정값
            }
            filtered = self._apply_filter(system_info, self.info_filters)

        except Exception as e:
            print(f'[ERROR] 시스템 정보 수집 중 오류 발생: {e}')
            filtered = {}

        print('\n===== Mission Computer Info =====')
        print(json.dumps(filtered, indent=4))
        print('=================================\n')

    def get_mission_computer_load(self):
        try:
            # 더미 데이터: 실제 센서 대신 임의 값으로 미션 컴퓨터 부하를 시뮬레이션
            cpu_percent = round(random.uniform(0.0, 100.0), 1)
            memory_percent = round(random.uniform(0.0, 100.0), 1)

            load_info = {
                'cpu_usage': f'{cpu_percent} %',
                'memory_usage': f'{memory_percent} %'
            }
            filtered = self._apply_filter(load_info, self.load_filters)

        except Exception as e:
            print(f'[ERROR] 시스템 부하 수집 중 오류 발생: {e}')
            filtered = {}

        print('\n===== Mission Computer Load =====')
        print(json.dumps(filtered, indent=4))
        print('=================================\n')


# 실행 영역 : Java의 main 메소드와 유사한 역할
if __name__ == '__main__':
    runComputer = MissionComputer()  # 객체 생성
    runComputer.get_mission_computer_info()  # 시스템 정보 출력
    runComputer.get_mission_computer_load()  # 실시간 부하 출력