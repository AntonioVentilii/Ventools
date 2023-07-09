import sys
import time

import pyautogui
from screeninfo import get_monitors


def run_loop():
    n = 2
    monitors = get_monitors()
    chosen_monitor = [m for m in monitors if m.name.endswith(f'DISPLAY{n}')][0]
    x = chosen_monitor.x
    y = chosen_monitor.y
    interval = 60 * 4
    while not pyautogui.position() == (0, 0):
        pyautogui.moveTo(x + 100, y + 1000, duration=3)
        pyautogui.moveTo(x + 1, y + 100, duration=3)
        pyautogui.click()
        for i in range(interval):
            sys.stdout.write(f'\rNext iteration in {interval - i} seconds...')
            sys.stdout.flush()
            time.sleep(1)


def wake_up():
    while True:
        pos_before = pyautogui.position()
        time.sleep(60 * 4)
        pos_after = pyautogui.position()
        if pos_before == pos_after:
            pyautogui.press('volumedown')
            time.sleep(1)
            pyautogui.press('volumeup')


if __name__ == '__main__':
    wake_up()
    # run_loop()
    print('Done')
