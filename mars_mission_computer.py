import random

class DummySensor:
    def __init__(self): #generator : JAVA와 다르게 필드로 선언하고 Generator에서 초기화를 하는게 아닌
        self.env_values = {         # 선언, 초기화를 한 번에 진행
            'mars_base_internal_temperature': 0.0,
            'mars_base_external_temperature': 0.0,
            'mars_base_internal_humidity': 0.0,
            'mars_base_external_illuminance': 0.0,
            'mars_base_internal_co2': 0.0,
            'mars_base_internal_oxygen': 0.0
        }
    def EnvironSet(self):
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2) # 실수값이라 Uniform 사용
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2) # 일반적으로 random.randint << 정수형
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2) # 2번째자리에서 round
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def getEnvironment(self): #getter Method
        return self.env_values # Python에서는 self를 명시 (객체에서 부르는 메소드라도 본인 객체는 넘어감을 명시)
                                # JAVA에선 없는 개념 : JAVA는 자동으로 가려줌.

if __name__ == '__main__':
    DummySensor = DummySensor()

    DummySensor.EnvironSet()
    CurrentEnvironment = DummySensor.getEnvironment()

    for key, value in CurrentEnvironment.items():
        print(f'{key} : {value}')