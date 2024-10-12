from multiprocessing import Pool, cpu_count, current_process
import logging
from time import time


logger = logging.getLogger()
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


# Синхронна версія
def sync_factorize(*number):
    result = []
    for num in (number):
        res = []
        for n in range(1, num + 1):
            if num % n == 0:
                res.append(n)
        result.append(res)

    return result


def factor(number: int) -> list:
    result = []
    t = time()
    for num in range(1, number + 1):
        if number % num == 0:
            result.append(num)
    logger.debug(f'Process:{current_process().name} for number: {
                 number} take {time() - t} seconds')
    return result


def factorize(*number):
    with Pool(processes=cpu_count()) as pool:
        result = pool.map(factor, [128, 255, 99999, 10651060])

    return result


if __name__ == '__main__':

    t = time()
    a, b, c, d = sync_factorize(128, 255, 99999, 10651060)
    logger.debug(f'\nРозрахунок синнхронною функцією зайняв: {
                 time() - t} секунд')
    ta = time()
    a, b, c, d = factorize(128, 255, 99999, 10651060)
    logger.debug(
        f'\nРозрахунок асиннхронною функцією зайняв: {time() - ta} секунд')
    # print('#', a)
    # print('#', b)
    # print('#', c)
    assert a == [1, 2, 4, 8, 16, 32, 64, 128]
    assert b == [1, 3, 5, 15, 17, 51, 85, 255]
    assert c == [1, 3, 9, 41, 123, 271, 369, 813, 2439, 11111, 33333, 99999]
    assert d == [1, 2, 4, 5, 7, 10, 14, 20, 28, 35, 70, 140, 76079, 152158, 304316,
                 380395, 532553, 760790, 1065106, 1521580, 2130212, 2662765, 5325530, 10651060]
