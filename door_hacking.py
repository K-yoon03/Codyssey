"""
door_hacking_gpu.py

Mars Base Emergency Storage - GPU(OpenCL) ZIP Password Cracker
==============================================================
AMD iGPU (gfx90c / Vega) 기준.

Author : kyoon
Python : 3.x
Style  : PEP 8
"""

import struct
import string
import time
import zipfile
import numpy as np
from datetime import datetime

try:
    import pyopencl as cl
    OPENCL_AVAILABLE = True
except ImportError:
    OPENCL_AVAILABLE = False


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
ZIP_FILE = 'emergency_storage_key.zip'
PASSWORD_FILE = 'password.txt'
CHARSET = string.digits + string.ascii_lowercase
PASSWORD_LENGTH = 6
TOTAL_CASES = len(CHARSET) ** PASSWORD_LENGTH   # 36^6

BATCH_SIZE = 8_000_000
MAX_CANDIDATES = BATCH_SIZE // 256 * 2 + 1000


# ---------------------------------------------------------------------------
# OpenCL 커널
# ---------------------------------------------------------------------------
KERNEL_SOURCE = r"""
__constant uint CRC_TABLE[256] = {
    0x00000000u, 0x77073096u, 0xEE0E612Cu, 0x990951BAu,
    0x076DC419u, 0x706AF48Fu, 0xE963A535u, 0x9E6495A3u,
    0x0EDB8832u, 0x79DCB8A4u, 0xE0D5E91Eu, 0x97D2D988u,
    0x09B64C2Bu, 0x7EB17CBDu, 0xE7B82D07u, 0x90BF1D91u,
    0x1DB71064u, 0x6AB020F2u, 0xF3B97148u, 0x84BE41DEu,
    0x1ADAD47Du, 0x6DDDE4EBu, 0xF4D4B551u, 0x83D385C7u,
    0x136C9856u, 0x646BA8C0u, 0xFD62F97Au, 0x8A65C9ECu,
    0x14015C4Fu, 0x63066CD9u, 0xFA0F3D63u, 0x8D080DF5u,
    0x3B6E20C8u, 0x4C69105Eu, 0xD56041E4u, 0xA2677172u,
    0x3C03E4D1u, 0x4B04D447u, 0xD20D85FDu, 0xA50AB56Bu,
    0x35B5A8FAu, 0x42B2986Cu, 0xDBBBC9D6u, 0xACBCF940u,
    0x32D86CE3u, 0x45DF5C75u, 0xDCD60DCFu, 0xABD13D59u,
    0x26D930ACu, 0x51DE003Au, 0xC8D75180u, 0xBFD06116u,
    0x21B4F4B5u, 0x56B3C423u, 0xCFBA9599u, 0xB8BDA50Fu,
    0x2802B89Eu, 0x5F058808u, 0xC60CD9B2u, 0xB10BE924u,
    0x2F6F7C87u, 0x58684C11u, 0xC1611DABu, 0xB6662D3Du,
    0x76DC4190u, 0x01DB7106u, 0x98D220BCu, 0xEFD5102Au,
    0x71B18589u, 0x06B6B51Fu, 0x9FBFE4A5u, 0xE8B8D433u,
    0x7807C9A2u, 0x0F00F934u, 0x9609A88Eu, 0xE10E9818u,
    0x7F6A0DBBu, 0x086D3D2Du, 0x91646C97u, 0xE6635C01u,
    0x6B6B51F4u, 0x1C6C6162u, 0x856530D8u, 0xF262004Eu,
    0x6C0695EDu, 0x1B01A57Bu, 0x8208F4C1u, 0xF50FC457u,
    0x65B0D9C6u, 0x12B7E950u, 0x8BBEB8EAu, 0xFCB9887Cu,
    0x62DD1DDFu, 0x15DA2D49u, 0x8CD37CF3u, 0xFBD44C65u,
    0x4DB26158u, 0x3AB551CEu, 0xA3BC0074u, 0xD4BB30E2u,
    0x4ADFA541u, 0x3DD895D7u, 0xA4D1C46Du, 0xD3D6F4FBu,
    0x4369E96Au, 0x346ED9FCu, 0xAD678846u, 0xDA60B8D0u,
    0x44042D73u, 0x33031DE5u, 0xAA0A4C5Fu, 0xDD0D7CC9u,
    0x5005713Cu, 0x270241AAu, 0xBE0B1010u, 0xC90C2086u,
    0x5768B525u, 0x206F85B3u, 0xB966D409u, 0xCE61E49Fu,
    0x5EDEF90Eu, 0x29D9C998u, 0xB0D09822u, 0xC7D7A8B4u,
    0x59B33D17u, 0x2EB40D81u, 0xB7BD5C3Bu, 0xC0BA6CADu,
    0xEDB88320u, 0x9ABFB3B6u, 0x03B6E20Cu, 0x74B1D29Au,
    0xEAD54739u, 0x9DD277AFu, 0x04DB2615u, 0x73DC1683u,
    0xE3630B12u, 0x94643B84u, 0x0D6D6A3Eu, 0x7A6A5AA8u,
    0xE40ECF0Bu, 0x9309FF9Du, 0x0A00AE27u, 0x7D079EB1u,
    0xF00F9344u, 0x8708A3D2u, 0x1E01F268u, 0x6906C2FEu,
    0xF762575Du, 0x806567CBu, 0x196C3671u, 0x6E6B06E7u,
    0xFED41B76u, 0x89D32BE0u, 0x10DA7A5Au, 0x67DD4ACCu,
    0xF9B9DF6Fu, 0x8EBEEFF9u, 0x17B7BE43u, 0x60B08ED5u,
    0xD6D6A3E8u, 0xA1D1937Eu, 0x38D8C2C4u, 0x4FDFF252u,
    0xD1BB67F1u, 0xA6BC5767u, 0x3FB506DDu, 0x48B2364Bu,
    0xD80D2BDAu, 0xAF0A1B4Cu, 0x36034AF6u, 0x41047A60u,
    0xDF60EFC3u, 0xA867DF55u, 0x316E8EEFu, 0x4669BE79u,
    0xCB61B38Cu, 0xBC66831Au, 0x256FD2A0u, 0x5268E236u,
    0xCC0C7795u, 0xBB0B4703u, 0x220216B9u, 0x5505262Fu,
    0xC5BA3BBEu, 0xB2BD0B28u, 0x2BB45A92u, 0x5CB36A04u,
    0xC2D7FFA7u, 0xB5D0CF31u, 0x2CD99E8Bu, 0x5BDEAE1Du,
    0x9B64C2B0u, 0xEC63F226u, 0x756AA39Cu, 0x026D930Au,
    0x9C0906A9u, 0xEB0E363Fu, 0x72076785u, 0x05005713u,
    0x95BF4A82u, 0xE2B87A14u, 0x7BB12BAEu, 0x0CB61B38u,
    0x92D28E9Bu, 0xE5D5BE0Du, 0x7CDCEFB7u, 0x0BDBDF21u,
    0x86D3D2D4u, 0xF1D4E242u, 0x68DDB3F8u, 0x1FDA836Eu,
    0x81BE16CDu, 0xF6B9265Bu, 0x6FB077E1u, 0x18B74777u,
    0x88085AE6u, 0xFF0F6A70u, 0x66063BCAu, 0x11010B5Cu,
    0x8F659EFFu, 0xF862AE69u, 0x616BFFD3u, 0x166CCF45u,
    0xA00AE278u, 0xD70DD2EEu, 0x4E048354u, 0x3903B3C2u,
    0xA7672661u, 0xD06016F7u, 0x4969474Du, 0x3E6E77DBu,
    0xAED16A4Au, 0xD9D65ADCu, 0x40DF0B66u, 0x37D83BF0u,
    0xA9BCAE53u, 0xDEBB9EC5u, 0x47B2CF7Fu, 0x30B5FFE9u,
    0xBDBDF21Cu, 0xCABAC28Au, 0x53B39330u, 0x24B4A3A6u,
    0xBAD03605u, 0xCDD70693u, 0x54DE5729u, 0x23D967BFu,
    0xB3667A2Eu, 0xC4614AB8u, 0x5D681B02u, 0x2A6F2B94u,
    0xB40BBE37u, 0xC30C8EA1u, 0x5A05DF1Bu, 0x2D02EF8Du,
};

#define CRC32B(crc, b) \
    (((crc) >> 8) ^ CRC_TABLE[((crc) ^ (uint)(b)) & 0xFFu])

#define UPDATE_KEYS(k0, k1, k2, b)                          \
    do {                                                     \
        (k0) = CRC32B((k0), (b));                            \
        (k1) = ((k1) + ((k0) & 0xFFu)) & 0xFFFFFFFFu;      \
        (k1) = ((k1) * 134775813u + 1u) & 0xFFFFFFFFu;     \
        (k2) = CRC32B((k2), (k1) >> 24);                    \
    } while (0)

#define STREAM_BYTE(k2) \
    (((((k2) | 2u) & 0xFFFFu) * (((k2) | 2u) ^ 1u)) >> 8 & 0xFFu)

__kernel void collect_candidates(
    __global const uchar *enc_data,
    __global const uchar *charset,
    const    uint         cs_len,
    const    uint         batch_lo,
    const    uint         batch_hi,
    const    uint         batch_sz,
    const    uchar        check_byte,
    __global uint        *candidates,
    const    uint         max_candidates
)
{
    uint gid = get_global_id(0);
    if (gid >= batch_sz) return;

    ulong start_idx = ((ulong)batch_hi << 32) | (ulong)batch_lo;
    ulong idx = start_idx + (ulong)gid;
    if (idx >= 2176782336ul) return;

    uchar pw[6];
    ulong tmp = idx;
    for (int i = 5; i >= 0; i--) {
        pw[i] = charset[tmp % cs_len];
        tmp /= cs_len;
    }

    uint k0 = 0x12345678u, k1 = 0x23456789u, k2 = 0x34567890u;
    for (int i = 0; i < 6; i++) {
        UPDATE_KEYS(k0, k1, k2, (uint)pw[i]);
    }

    uchar db = 0;
    for (int i = 0; i < 12; i++) {
        db = enc_data[i] ^ (uchar)STREAM_BYTE(k2);
        UPDATE_KEYS(k0, k1, k2, (uint)db);
    }
    if (db != check_byte) return;

    uint slot = atom_add(&candidates[0], 1u);
    if (slot < max_candidates - 1u) {
        candidates[slot + 1] = (uint)idx;
    }
}
"""


# ---------------------------------------------------------------------------
# ZIP 정보 추출
# ---------------------------------------------------------------------------
def _read_zip_enc_data(zip_path):
    with open(zip_path, 'rb') as f:
        raw = f.read()

    lh = raw.find(b'PK\x03\x04')
    fname_len = struct.unpack_from('<H', raw, lh + 26)[0]
    extra_len = struct.unpack_from('<H', raw, lh + 28)[0]
    data_start = lh + 30 + fname_len + extra_len
    compress_size = struct.unpack_from('<I', raw, lh + 18)[0]

    flags = struct.unpack_from('<H', raw, lh + 6)[0]
    mod_time = struct.unpack_from('<H', raw, lh + 10)[0]
    cd = raw.rfind(b'PK\x01\x02')
    target_crc = struct.unpack_from('<I', raw, cd + 16)[0]

    enc_data = raw[data_start:data_start + compress_size]

    # flag bit3=1 이면 항상 mod_time 상위 바이트가 check byte
    if flags & 0x8:
        check_byte = (mod_time >> 8) & 0xFF
    else:
        check_byte = (target_crc >> 24) & 0xFF

    return enc_data, check_byte


# ---------------------------------------------------------------------------
# 인덱스 -> 암호
# ---------------------------------------------------------------------------
def _idx_to_password(idx):
    n = len(CHARSET)
    chars = []
    for _ in range(PASSWORD_LENGTH):
        chars.append(CHARSET[idx % n])
        idx //= n
    return ''.join(reversed(chars))


# ---------------------------------------------------------------------------
# GPU 크래커
# ---------------------------------------------------------------------------
def unlock_zip_gpu(zip_path=ZIP_FILE, batch_size=BATCH_SIZE):
    """
    GPU 로 check byte 후보를 수집하고 CPU 로 zipfile 최종 검증한다.

    Args:
        zip_path  : ZIP 파일 경로.
        batch_size: 커널 1회 처리 후보 수.

    Returns:
        성공 시 암호 문자열, 실패 시 None.
    """
    if not OPENCL_AVAILABLE:
        print('[ERROR] pip install pyopencl')
        return None

    try:
        enc_data, check_byte = _read_zip_enc_data(zip_path)
    except FileNotFoundError:
        print('[ERROR] 파일을 찾을 수 없습니다: ' + zip_path)
        return None
    except Exception as e:
        print('[ERROR] ZIP 분석 실패: ' + str(e))
        return None

    device = None
    dev_name = ''
    for platform in cl.get_platforms():
        devs = platform.get_devices(cl.device_type.GPU)
        if devs:
            device = devs[0]
            dev_name = device.name.strip()
            break
    if device is None:
        print('[ERROR] GPU 장치를 찾을 수 없습니다.')
        return None

    ctx = cl.Context([device])
    queue = cl.CommandQueue(ctx)

    try:
        program = cl.Program(ctx, KERNEL_SOURCE).build()
    except Exception as e:
        print('[ERROR] 커널 컴파일 실패:\n' + str(e))
        return None

    kernel = cl.Kernel(program, 'collect_candidates')

    mf = cl.mem_flags
    enc_np = np.frombuffer(enc_data, dtype=np.uint8)
    cs_np = np.frombuffer(CHARSET.encode('ascii'), dtype=np.uint8)
    enc_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=enc_np)
    cs_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=cs_np)

    max_cands = MAX_CANDIDATES
    cand_np = np.zeros(max_cands + 1, dtype=np.uint32)
    cand_buf = cl.Buffer(ctx, mf.READ_WRITE, size=cand_np.nbytes)

    start_dt = datetime.now()
    start_ts = time.time()

    print('=' * 62)
    print('  Mars Base -- Emergency Storage Unlock  [GPU / OpenCL]')
    print('=' * 62)
    print('  장치       : ' + dev_name)
    print('  대상 파일  : ' + zip_path)
    print('  총 후보 수 : ' + format(TOTAL_CASES, ','))
    print('  배치 크기  : ' + format(batch_size, ','))
    print('  check byte : ' + hex(check_byte))
    print('  시작 시각  : ' + start_dt.strftime('%Y-%m-%d %H:%M:%S'))
    print('=' * 62)

    found = None

    with zipfile.ZipFile(zip_path) as zf:
        target_file = zf.namelist()[0]

        for batch_start in range(0, TOTAL_CASES, batch_size):
            cur_batch = min(batch_size, TOTAL_CASES - batch_start)
            batch_lo = np.uint32(batch_start & 0xFFFFFFFF)
            batch_hi = np.uint32(batch_start >> 32)

            cl.enqueue_copy(queue, cand_buf,
                            np.zeros(max_cands + 1, dtype=np.uint32))
            queue.finish()

            kernel.set_args(
                enc_buf,
                cs_buf,
                np.uint32(len(CHARSET)),
                batch_lo,
                batch_hi,
                np.uint32(cur_batch),
                np.uint8(check_byte),
                cand_buf,
                np.uint32(max_cands),
            )
            cl.enqueue_nd_range_kernel(queue, kernel, (int(cur_batch),), None)
            queue.finish()

            cl.enqueue_copy(queue, cand_np, cand_buf)
            queue.finish()

            count = int(cand_np[0])

            for i in range(min(count, max_cands)):
                pw = _idx_to_password(int(cand_np[i + 1]))
                try:
                    zf.read(target_file, pwd=pw.encode())
                    found = pw
                    break
                except Exception:
                    pass

            elapsed = time.time() - start_ts
            searched = batch_start + cur_batch
            speed = searched / elapsed if elapsed > 0 else 0
            progress = searched / TOTAL_CASES * 100
            print(
                '  [' + format(searched, '>13,') + '회 / '
                + format(progress, '5.2f') + '%]'
                + '  후보: ' + format(count, '>6,') + '개'
                + '  경과: ' + format(elapsed, '6.1f') + 's'
                + '  속도: ' + format(int(speed), ',') + ' pw/s'
            )

            if found:
                break

    elapsed_total = time.time() - start_ts

    if found:
        print()
        print('=' * 62)
        print('  [SUCCESS] 암호 발견!')
        print('  암호      : ' + found)
        print('  소요 시간 : ' + format(elapsed_total, '.2f') + ' 초')
        print('=' * 62)
        try:
            with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
                f.write(found)
            print("  암호가 '" + PASSWORD_FILE + "' 에 저장되었습니다.")
        except OSError as e:
            print('[ERROR] 파일 저장 실패: ' + str(e))
    else:
        print()
        print('=' * 62)
        print('  [FAIL] 전체 탐색 완료, 암호를 찾지 못했습니다.')
        print('  소요 시간 : ' + format(elapsed_total, '.2f') + ' 초')
        print('=' * 62)

    return found


# ---------------------------------------------------------------------------
# 실행 진입점
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    unlock_zip_gpu(ZIP_FILE, batch_size=BATCH_SIZE)