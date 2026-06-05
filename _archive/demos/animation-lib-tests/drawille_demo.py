import math
import time
from drawille import Canvas

# Orbiting dot around a ring using braille pixels

c = Canvas()
radius = 12
t = 0.0

def render() -> None:
    global t
    c.clear()
    # Draw ring
    for i in range(96):
        a = i * (2 * math.pi / 96)
        x = int(radius * math.cos(a))
        y = int(radius * math.sin(a))
        c.set(x, y)
    # Moving dot
    x = int(radius * math.cos(t))
    y = int(radius * math.sin(t))
    c.set(x, y)
    t += 0.12
    # ANSI clear + draw
    print("\x1b[H\x1b[2J" + c.frame())

def main() -> None:
    while True:
        render()
        time.sleep(0.05)

if __name__ == "__main__":
    main()


