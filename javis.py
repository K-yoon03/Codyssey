"""
javis.py

Mars Base Voice Recorder & STT
================================
마이크를 인식하고 음성을 녹음하여 records 폴더에 저장한다.
녹음된 WAV 파일을 STT(Speech to Text)로 변환하고 CSV로 저장한다.

파일명 형식: 년월일-시간분초.wav  (예: 20260515-142530.wav)
CSV  형식 : 년월일-시간분초.csv

[필요 패키지 설치]
  pip install pyaudio SpeechRecognition

Author : kyoon
Python : 3.x
Style  : PEP 8
"""

import csv
import datetime
import os
import threading
import wave

try:
    import pyaudio
except ImportError:
    print('[ERROR] pyaudio 가 설치되지 않았습니다.')
    print('  pip install pyaudio  후 재실행하세요.')
    raise SystemExit(1)

try:
    import speech_recognition as sr
except ImportError:
    print('[ERROR] SpeechRecognition 이 설치되지 않았습니다.')
    print('  pip install SpeechRecognition  후 재실행하세요.')
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
RECORDS_DIR = 'records'
SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_FORMAT = pyaudio.paInt16
CHUNK = 1024
STT_LANGUAGE = 'ko-KR'    # 한국어 인식 (영어: 'en-US')


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
# STT 기능
# ---------------------------------------------------------------------------
class SpeechToText:
    """
    WAV 파일을 텍스트로 변환하고 CSV로 저장하는 클래스.

    SpeechRecognition 라이브러리의 Google Web Speech API를 사용한다.
    인터넷 연결이 필요하다.
    """

    def __init__(self):
        self._recognizer = sr.Recognizer()

    def list_wav_files(self):
        """
        records 폴더의 WAV 파일 목록을 반환한다.

        Returns:
            WAV 파일명 리스트 (정렬됨).
        """
        if not os.path.exists(RECORDS_DIR):
            return []
        try:
            files = sorted([
                f for f in os.listdir(RECORDS_DIR)
                if f.endswith('.wav')
            ])
        except OSError as e:
            print('[ERROR] 폴더 읽기 실패: ' + str(e))
            return []
        return files

    def transcribe_file(self, wav_path):
        """
        WAV 파일을 STT로 변환하여 (시간, 텍스트) 튜플 리스트를 반환한다.

        파일을 청크 단위로 분할하여 각 구간의 시작 시간과 텍스트를 추출한다.

        Args:
            wav_path: 변환할 WAV 파일 경로.

        Returns:
            [(시간_문자열, 인식된_텍스트), ...] 리스트. 실패 시 빈 리스트.
        """
        results = []

        try:
            with sr.AudioFile(wav_path) as source:
                # 파일 전체 길이 확인
                recognizer = self._recognizer
                audio_length = source.DURATION
                chunk_size = 10   # 10초 단위로 분할

                offset = 0.0
                while offset < audio_length:
                    duration = min(chunk_size, audio_length - offset)
                    try:
                        audio_chunk = recognizer.record(
                            source,
                            duration=duration,
                            offset=0 if offset == 0 else None
                        )
                        text = recognizer.recognize_google(
                            audio_chunk,
                            language=STT_LANGUAGE
                        )
                        time_str = str(datetime.timedelta(seconds=int(offset)))
                        results.append((time_str, text))
                        print('    [{}] {}'.format(time_str, text))
                    except sr.UnknownValueError:
                        time_str = str(datetime.timedelta(seconds=int(offset)))
                        results.append((time_str, '(인식 불가)'))
                        print('    [{}] (인식 불가)'.format(time_str))
                    except sr.RequestError as e:
                        print('[ERROR] STT API 오류: ' + str(e))
                        break
                    offset += chunk_size

        except OSError as e:
            print('[ERROR] 파일 읽기 실패: ' + str(e))
            return []

        return results

    def transcribe_and_save(self, wav_filename):
        """
        WAV 파일을 STT로 변환하고 동일한 이름의 CSV 파일로 저장한다.

        CSV 컬럼: 시간, 텍스트

        Args:
            wav_filename: records 폴더 내 WAV 파일명 (경로 제외).

        Returns:
            저장된 CSV 경로. 실패 시 None.
        """
        wav_path = os.path.join(RECORDS_DIR, wav_filename)
        csv_filename = wav_filename.replace('.wav', '.csv')
        csv_path = os.path.join(RECORDS_DIR, csv_filename)

        if not os.path.exists(wav_path):
            print('[ERROR] 파일을 찾을 수 없습니다: ' + wav_path)
            return None

        print()
        print("  STT 변환 중: '{}'".format(wav_filename))
        print('  ' + '-' * 40)

        results = self.transcribe_file(wav_path)
        if not results:
            print('  변환된 텍스트가 없습니다.')
            return None

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['시간', '텍스트'])
                writer.writerows(results)
            print('  ' + '-' * 40)
            print("  CSV 저장 완료: '{}'".format(csv_path))
            return csv_path
        except OSError as e:
            print('[ERROR] CSV 저장 실패: ' + str(e))
            return None

    def transcribe_all(self):
        """records 폴더의 모든 WAV 파일을 STT 변환한다."""
        wav_files = self.list_wav_files()
        if not wav_files:
            print('  변환할 WAV 파일이 없습니다.')
            return

        print()
        print('  총 {}개 파일을 변환합니다.'.format(len(wav_files)))
        for fname in wav_files:
            self.transcribe_and_save(fname)


# ---------------------------------------------------------------------------
# 보너스: CSV 키워드 검색
# ---------------------------------------------------------------------------
def search_keyword(keyword):
    """
    records 폴더의 모든 CSV 파일에서 키워드를 검색하여 출력한다.

    Args:
        keyword: 검색할 키워드 문자열.
    """
    if not os.path.exists(RECORDS_DIR):
        print('  records 폴더가 없습니다.')
        return

    try:
        csv_files = sorted([
            f for f in os.listdir(RECORDS_DIR)
            if f.endswith('.csv')
        ])
    except OSError as e:
        print('[ERROR] 폴더 읽기 실패: ' + str(e))
        return

    if not csv_files:
        print('  검색할 CSV 파일이 없습니다.')
        return

    print()
    print("  키워드 '{}' 검색 결과:".format(keyword))
    print('  ' + '-' * 40)

    found_count = 0
    for fname in csv_files:
        fpath = os.path.join(RECORDS_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)   # 헤더 건너뜀
                for row in reader:
                    if len(row) >= 2 and keyword.lower() in row[1].lower():
                        print('  [{}] 시간: {}  내용: {}'.format(
                            fname, row[0], row[1]))
                        found_count += 1
        except OSError as e:
            print('[ERROR] 파일 읽기 실패 {}: {}'.format(fname, str(e)))

    if found_count == 0:
        print("  '{}' 를 포함한 내용이 없습니다.".format(keyword))
    else:
        print('  ' + '-' * 40)
        print('  총 {}건 발견'.format(found_count))


# ---------------------------------------------------------------------------
# 보너스: 날짜 범위로 녹음 파일 목록 조회
# ---------------------------------------------------------------------------
def list_records_by_date(start_date, end_date):
    """
    start_date ~ end_date 범위의 녹음 파일 목록을 출력한다.

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
    print('  JAVIS - Mars Base Voice Recorder & STT')
    print('=' * 50)

    recorder = VoiceRecorder()
    stt = SpeechToText()

    while True:
        print()
        print('  [메뉴]')
        print('  1. 마이크 목록 확인')
        print('  2. 녹음 시작 (수동 종료)')
        print('  3. 녹음 시작 (시간 지정)')
        print('  4. STT 변환 - 파일 선택')
        print('  5. STT 변환 - 전체 파일')
        print('  6. 날짜 범위로 파일 조회')
        print('  7. 키워드 검색 (보너스)')
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
            wav_files = stt.list_wav_files()
            if not wav_files:
                print('  WAV 파일이 없습니다.')
                continue
            print()
            for i, f in enumerate(wav_files, start=1):
                print('  [{:>2}] {}'.format(i, f))
            try:
                num = int(input('  번호 선택: ').strip())
                if not 1 <= num <= len(wav_files):
                    print('[ERROR] 올바른 번호를 입력하세요.')
                    continue
            except ValueError:
                print('[ERROR] 숫자를 입력하세요.')
                continue
            stt.transcribe_and_save(wav_files[num - 1])

        elif choice == '5':
            stt.transcribe_all()

        elif choice == '6':
            try:
                start = input('  시작 날짜 (YYYYMMDD): ').strip()
                end = input('  종료 날짜 (YYYYMMDD): ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            list_records_by_date(start, end)

        elif choice == '7':
            try:
                keyword = input('  검색할 키워드: ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if keyword:
                search_keyword(keyword)
            else:
                print('  키워드를 입력하세요.')

        elif choice == '0':
            print()
            print('  종료합니다.')
            break

        else:
            print('  올바른 번호를 입력하세요.')

    recorder.close()


if __name__ == '__main__':
    main()