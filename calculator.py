import sys  # sys 모듈은 이용한 프로그램 Life Cycle 제어

from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
# UI 구성을 위한 PyQt5 import


class Calculator(QWidget):  # Qwidget을 상속받아 계산기 UI를 생성하는 클래스
    def __init__(self):
        super().__init__()  # 상속받은 부모 클래스 초기화
        self.setWindowTitle('Calculator')
        self.setFixedSize(300, 400)

        # 처음 화면을 켰을 때 나와있는 최초 숫자
        self.display = QLabel('0')
        # 텍스트 정렬
        self.display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # 글씨 크기 및 padding 설정
        self.display.setStyleSheet('font-size: 30px; padding: 10px;')

        self.current_text = '0'  # 현재 입력된 값을 문자열로 저장하는 변수 초기화

        self.init_ui()  # UI 구성 함수 호출

    def init_ui(self): # 화면 UI 설계 함수
        grid = QGridLayout()  # 버튼을 배치하기 위해 Grid로 레이아웃을 선택
        grid.addWidget(self.display, 0, 0, 1, 4)  
        # 출력창의 첫 행에 배치하며, 4칸을 사용

        # 버튼에 들어갈 내용이 담긴 배열
        buttons = [
            ['AC', '+/-', '%', '÷'],
            ['7', '8', '9', '×'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '.', '=']
        ]

        # buttons 배열에 담긴 내용으로 버튼 생성 및 이벤트 연결
        for row, line in enumerate(buttons, start=1):  # 1행부터 시작
            for col, text in enumerate(line):
                button = QPushButton(text)  # 버튼 생성
                button.setFixedSize(60, 60)  # 버튼 크기 설정
                button.clicked.connect(self.button_clicked)  
                # 버튼 클릭 시 button_clicked 함수 호출

                grid.addWidget(button, row, col)  # 버튼 배치

        self.setLayout(grid)  # 레이아웃을 윈도우에 적용

    # 버튼 클릭 시 호출할 함수
    def button_clicked(self):
        sender = self.sender()  # 클릭된 버튼 객체 가져오기
        text = sender.text()  # 버튼에 표시된 텍스트 가져오기

        if text == 'AC':  # 전체 초기화 버튼
            self.current_text = '0'  # 값 초기화

        elif text == '=':  # 계산 실행 버튼
            try:
                # 화면상 x, ÷ 기호를 실질적 Python의 연산자로 변경
                expression = self.current_text.replace('×', '*').replace('÷', '/')
                # eval을 사용해 문자열에 담긴 수식을 계산하고 다시 문자열로 저장
                ''' ! Eval이란?
                        문자열로 된 표현식을 입력받아 실행하는 내장함수
                        보안상의 이유로 사용을 권장하지 않음.
                '''
                self.current_text = str(eval(expression))

            except Exception:
                # 잘못된 수식일 경우 에러 표시
                # Ex) ZeroDivision 같은 불가능한 수식일 경우
                self.current_text = 'Error'

        else:
            # 숫자 및 기타 버튼 입력 처리
            if self.current_text == '0':
                # 초기값이 0이면 새 입력으로 교체
                self.current_text = text
            else:
                # 기존 값 뒤에 이어붙이기
                self.current_text += text

        # 화면에 결과 출력
        self.display.setText(self.current_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)  # QApplication 객체 생성 (필수)
    '''
    sys.argv를 통하여 QApplication에게 명령어 인자값 넘김.
    ex) python calculator.py test
    입력값 ['calcualator.py', 'test']
    일반적으로 Qt의 실행 옵션 처리를 위하여 sys.argv를 통하여 넘겨주는게 보통이지만
    현재 해당 인자값을 이용한 내용이 없으므로 빈 배열을 넣어도 상관 X
    '''

    calc = Calculator()  # 계산기 객체 생성
    calc.show()  # 화면에 표시
    app.exec_()  # 이벤트 루프 실행