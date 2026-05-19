"""
caesar_cipher.py

Mars Base Emergency Storage - Caesar Cipher Decoder
====================================================
password.txt 의 카이사르 암호를 해독한다.

카이사르 암호: 알파벳을 일정 자리수만큼 밀어서 치환하는 암호화 기법.
예) 키=3 이면 A->D, B->E, ... Z->C

보너스: 영어 단어 사전으로 자동 감지 지원.

Author : kyoon
Python : 3.x
Style  : PEP 8
"""

PASSWORD_FILE = 'password.txt'
RESULT_FILE = 'result.txt'
ALPHABET_SIZE = 26

# 보너스: 간단한 영어 단어 사전
DICTIONARY = {
    'i', 'a', 'the', 'be', 'to', 'of', 'and', 'in', 'is', 'it',
    'you', 'that', 'he', 'she', 'we', 'they', 'do', 'at', 'but',
    'from', 'or', 'an', 'all', 'not', 'can', 'her', 'was', 'one',
    'our', 'had', 'by', 'words', 'love', 'mars', 'base', 'hello',
    'space', 'earth', 'planet', 'open', 'door', 'key', 'secret',
}


def caesar_cipher_decode(target_text):
    """
    카이사르 암호를 자리수 1~26 으로 순서대로 해독하여 출력한다.

    알파벳 대소문자만 자리수만큼 역방향으로 이동하고,
    공백 및 기타 문자는 그대로 유지한다.
    자리수마다 결과를 출력하여 눈으로 확인할 수 있다.

    사전에 있는 단어가 발견되면 즉시 반복을 멈추고 해당 결과를 반환한다.
    (보너스 기능)

    Args:
        target_text: 해독할 암호 문자열.

    Returns:
        (키, 해독된 문자열) 튜플. 사전 자동 감지 실패 시 None.
    """
    print('=' * 50)
    print('  Caesar Cipher Decoder')
    print('=' * 50)
    print('  암호문: ' + target_text)
    print('=' * 50)

    for shift in range(1, ALPHABET_SIZE + 1):
        decoded = ''
        for ch in target_text:
            if ch.isupper():
                decoded += chr((ord(ch) - ord('A') - shift) % ALPHABET_SIZE + ord('A'))
            elif ch.islower():
                decoded += chr((ord(ch) - ord('a') - shift) % ALPHABET_SIZE + ord('a'))
            else:
                decoded += ch

        print('  키 {:>2} : {}'.format(shift, decoded))

        # 보너스: 사전 단어 감지 시 자동 중단
        words = decoded.lower().split()
        matched = [w for w in words if w in DICTIONARY and len(w) >= 2]
        if matched:
            print()
            print('  [자동 감지] 키 {} 에서 사전 단어 발견: {}'.format(
                shift, ', '.join(matched)))
            return shift, decoded

    return None


def save_result(shift, decoded_text):
    """
    해독 결과를 result.txt 에 저장한다.

    Args:
        shift       : 해독에 사용된 키(자리수).
        decoded_text: 해독된 문자열.
    """
    try:
        with open(RESULT_FILE, 'w', encoding='utf-8') as f:
            f.write('카이사르 암호 해독 결과\n')
            f.write('=' * 30 + '\n')
            f.write('키(자리수) : {}\n'.format(shift))
            f.write('해독 결과  : {}\n'.format(decoded_text))
        print("  결과가 '{}' 에 저장되었습니다.".format(RESULT_FILE))
    except OSError as e:
        print('[ERROR] 파일 저장 실패: ' + str(e))


def main():
    # password.txt 읽기 (예외처리)
    try:
        with open(PASSWORD_FILE, 'r', encoding='utf-8') as f:
            target_text = f.read().strip()
    except FileNotFoundError:
        print('[ERROR] 파일을 찾을 수 없습니다: ' + PASSWORD_FILE)
        return
    except OSError as e:
        print('[ERROR] 파일 읽기 실패: ' + str(e))
        return

    # 암호 해독
    result = caesar_cipher_decode(target_text)

    print()
    print('=' * 50)

    if result:
        shift, decoded = result
        print('  [자동 감지 완료]')
        print('  키(자리수) : {}'.format(shift))
        print('  해독 결과  : {}'.format(decoded))
        save_result(shift, decoded)
    else:
        # 사전 감지 실패 시 수동 입력
        print('  사전에서 단어를 찾지 못했습니다.')
        print('  위 결과를 확인하고 키 번호를 입력하세요.')
        try:
            key_input = input('  키 번호 입력 (1~26): ').strip()
            shift = int(key_input)
            if not 1 <= shift <= ALPHABET_SIZE:
                print('[ERROR] 1~26 사이의 숫자를 입력하세요.')
                return
        except ValueError:
            print('[ERROR] 숫자를 입력하세요.')
            return

        # 선택한 키로 재해독
        decoded = ''
        for ch in target_text:
            if ch.isupper():
                decoded += chr((ord(ch) - ord('A') - shift) % ALPHABET_SIZE + ord('A'))
            elif ch.islower():
                decoded += chr((ord(ch) - ord('a') - shift) % ALPHABET_SIZE + ord('a'))
            else:
                decoded += ch

        print('  키(자리수) : {}'.format(shift))
        print('  해독 결과  : {}'.format(decoded))
        save_result(shift, decoded)

    print('=' * 50)


if __name__ == '__main__':
    main()