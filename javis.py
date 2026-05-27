"""
javis.py

Mars Base Voice Recorder
========================
마이크를 인식하고 음성을 녹음하여 records 폴더에 저장한다.
파일명 형식: 년월일-시간분초.wav  (예: 20260515-142530.wav)

[필요 패키지 설치]
  pip install pyaudio

Author : kyoon
Python : 3.x
Style  : PEP 8
"""

import os
import wave
import datetime

try:
    import pyaudio
except ImportError:
    print('[ERROR] pyaudio 가 설치되지 않았습니다.')
    print('  pip install pyaudio  후 재실행하세요.')
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
RECORDS_DIR = 'records'
SAMPLE_RATE = 44100       # 샘플레이트 (Hz)
CHANNELS = 1              # 모노 녹음
SAMPLE_FORMAT = pyaudio.paInt16
CHUNK = 1024              # 버퍼 크기


# ---------------------------------------------------------------------------
# 녹음 기능
# ---------------------------------------------------------------------------
class VoiceRecorder:
    """마이크를 인식하고 음성을 녹음하는 클래스."""

    def __init__(self):
        self._audio = pyaudio.PyAudio()
        self._ensure_records_dir()

    def _ensure_records_dir(self):
        """records 폴더가 없으면 생성한다."""
        try:
            if not os.path.exists(RECORDS_DIR):
                os.makedirs(RECORDS_DIR)
                print("  '{}' 폴더를 생성했습니다.".format(RECORDS_DIR))
        except OSError as e:
            print('[ERROR] 폴더 생성 실패: ' + str(e))
            raise

    def list_microphones(self):
        """
        시스템에서 사용 가능한 마이크 목록을 출력한다.

        Returns:
            사용 가능한 입력 장치 인덱스 리스트.
        """
        print()
        print('  [사용 가능한 마이크 목록]')
        print('  ' + '-' * 40)

        available = []
        for i in range(self._audio.get_device_count()):
            info = self._audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print('  [{:>2}] {}'.format(i, info['name']))
                available.append(i)

        if not available:
            print('  마이크를 찾을 수 없습니다.')
        print('  ' + '-' * 40)
        return available

    def record(self, device_index=None, duration=None):
        """
        마이크로 음성을 녹음하고 records 폴더에 저장한다.

        파일명은 '년월일-시간분초.wav' 형식으로 자동 생성된다.
        duration 이 None 이면 Enter 키 입력까지 계속 녹음한다.

        Args:
            device_index: 사용할 마이크 장치 인덱스 (None 이면 기본 장치).
            duration    : 녹음 시간 (초). None 이면 수동 종료.

        Returns:
            저장된 파일 경로 문자열. 실패 시 None.
        """
        now = datetime.datetime.now()
        filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'
        filepath = os.path.join(RECORDS_DIR, filename)

        print()
        print('  녹음 시작...')
        if duration:
            print('  {}초 후 자동 종료됩니다.'.format(duration))
        else:
            print('  Enter 키를 누르면 녹음이 종료됩니다.')

        frames = []

        try:
            stream = self._audio.open(
                format=SAMPLE_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK,
            )
        except OSError as e:
            print('[ERROR] 마이크 열기 실패: ' + str(e))
            return None

        if duration:
            total_chunks = int(SAMPLE_RATE / CHUNK * duration)
            for _ in range(total_chunks):
                frames.append(stream.read(CHUNK, exception_on_overflow=False))
        else:
            import threading

            stop_flag = [False]

            def wait_for_enter():
                input()
                stop_flag[0] = True

            t = threading.Thread(target=wait_for_enter, daemon=True)
            t.start()

            while not stop_flag[0]:
                frames.append(stream.read(CHUNK, exception_on_overflow=False))

        stream.stop_stream()
        stream.close()

        print('  녹음 종료.')

        # WAV 파일 저장
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self._audio.get_sample_size(SAMPLE_FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b''.join(frames))
            print("  저장 완료: '{}'".format(filepath))
            return filepath
        except OSError as e:
            print('[ERROR] 파일 저장 실패: ' + str(e))
            return None

    def close(self):
        """PyAudio 자원을 해제한다."""
        self._audio.terminate()


# ---------------------------------------------------------------------------
# 보너스: 날짜 범위로 녹음 파일 목록 조회
# ---------------------------------------------------------------------------
def list_records_by_date(start_date, end_date):
    """
    start_date ~ end_date 범위의 녹음 파일 목록을 출력한다.

    날짜 형식: 'YYYYMMDD'

    Args:
        start_date: 시작 날짜 문자열 (예: '20260501').
        end_date  : 종료 날짜 문자열 (예: '20260531').
    """
    try:
        start = datetime.datetime.strptime(start_date, '%Y%m%d')
        end = datetime.datetime.strptime(end_date, '%Y%m%d')
        end = end.replace(hour=23, minute=59, second=59)
    except ValueError:
        print('[ERROR] 날짜 형식이 올바르지 않습니다. (예: 20260501)')
        return

    if not os.path.exists(RECORDS_DIR):
        print('  records 폴더가 없습니다.')
        return

    try:
        files = sorted(os.listdir(RECORDS_DIR))
    except OSError as e:
        print('[ERROR] 폴더 읽기 실패: ' + str(e))
        return

    print()
    print('  [{} ~ {} 녹음 파일]'.format(start_date, end_date))
    print('  ' + '-' * 40)

    found = []
    for fname in files:
        if not fname.endswith('.wav'):
            continue
        try:
            file_dt = datetime.datetime.strptime(fname[:15], '%Y%m%d-%H%M%S')
            if start <= file_dt <= end:
                found.append(fname)
                print('  ' + fname)
        except ValueError:
            continue

    if not found:
        print('  해당 기간의 녹음 파일이 없습니다.')
    else:
        print('  총 {}개'.format(len(found)))
    print('  ' + '-' * 40)


# ---------------------------------------------------------------------------
# 메인 메뉴
# ---------------------------------------------------------------------------
def main():
    print('=' * 50)
    print('  JAVIS - Mars Base Voice Recorder')
    print('=' * 50)

    recorder = VoiceRecorder()

    while True:
        print()
        print('  [메뉴]')
        print('  1. 마이크 목록 확인')
        print('  2. 녹음 시작 (수동 종료)')
        print('  3. 녹음 시작 (시간 지정)')
        print('  4. 날짜 범위로 파일 조회 (보너스)')
        print('  0. 종료')
        print()

        choice = input('  선택: ').strip()

        if choice == '1':
            recorder.list_microphones()

        elif choice == '2':
            mics = recorder.list_microphones()
            if not mics:
                continue
            try:
                idx_input = input('  마이크 번호 입력 (기본값 Enter): ').strip()
                idx = int(idx_input) if idx_input else None
            except ValueError:
                print('[ERROR] 올바른 번호를 입력하세요.')
                continue
            recorder.record(device_index=idx)

        elif choice == '3':
            mics = recorder.list_microphones()
            if not mics:
                continue
            try:
                idx_input = input('  마이크 번호 입력 (기본값 Enter): ').strip()
                idx = int(idx_input) if idx_input else None
                sec_input = input('  녹음 시간(초) 입력: ').strip()
                sec = int(sec_input)
            except ValueError:
                print('[ERROR] 올바른 값을 입력하세요.')
                continue
            recorder.record(device_index=idx, duration=sec)

        elif choice == '4':
            try:
                start = input('  시작 날짜 (YYYYMMDD): ').strip()
                end = input('  종료 날짜 (YYYYMMDD): ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            list_records_by_date(start, end)

        elif choice == '0':
            print()
            print('  종료합니다.')
            break

        else:
            print('  올바른 번호를 입력하세요.')

    recorder.close()


if __name__ == '__main__':
    main()