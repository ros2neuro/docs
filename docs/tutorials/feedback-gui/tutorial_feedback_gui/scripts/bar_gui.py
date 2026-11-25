#!/usr/bin/env python3
"""A bar that follows the band power of one channel.

It listens to /bandpower (Float32MultiArray, one value per channel) and draws the value of one channel as a bar.
"""
import tkinter as tk

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

WIDTH, HEIGHT = 160, 420      # size of the window
MARGIN = 20                   # space around the bar


# --8<-- [start:normalize]
def normalize(value, minimum, maximum):
    """Map a band power from [minimum, maximum] to [0, 1]; what is outside is clipped."""
    if maximum <= minimum:
        return 0.0
    return min(1.0, max(0.0, (value - minimum) / (maximum - minimum)))
# --8<-- [end:normalize]


class BarGui(Node):
    def __init__(self):
        super().__init__('bar_gui')

        # --8<-- [start:parameters]
        self.declare_parameter('channel', 1)        # which channel to show: 1 is the first
        self.declare_parameter('minimum', 0.0)      # band power (ln uV^2) that gives an empty bar
        self.declare_parameter('maximum', 4.0)      # band power that gives a full bar
        # --8<-- [end:parameters]

        self.value = 0.0                            # the last value received, 0 to 1

        # --8<-- [start:subscription]
        self.create_subscription(Float32MultiArray, 'bandpower', self.on_bandpower, 10)
        # --8<-- [end:subscription]

        # --8<-- [start:window]
        self.root = tk.Tk()
        self.root.title('Band power')
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg='black', highlightthickness=0)
        self.canvas.pack()
        # an outline for the full scale, and the bar itself (we only change its height)
        self.canvas.create_rectangle(MARGIN, MARGIN, WIDTH - MARGIN, HEIGHT - MARGIN, outline='white')
        self.bar = self.canvas.create_rectangle(MARGIN, HEIGHT - MARGIN, WIDTH - MARGIN, HEIGHT - MARGIN,
                                                fill='deepskyblue', outline='')
        self.label = self.canvas.create_text(WIDTH // 2, HEIGHT - 5, fill='white', anchor='s', text='waiting...')
        # --8<-- [end:window]

    # --8<-- [start:callback]
    def on_bandpower(self, msg):
        """Called for every message: pick the channel and normalize it."""
        channel = self.get_parameter('channel').value
        if not 1 <= channel <= len(msg.data):
            self.get_logger().warn(f'channel {channel} is not in 1..{len(msg.data)}', throttle_duration_sec=2.0)
            return
        raw = msg.data[channel - 1]
        self.value = normalize(raw,
                               self.get_parameter('minimum').value,
                               self.get_parameter('maximum').value)
        self.canvas.itemconfigure(self.label, text=f'ch {channel}: {raw:.2f}')
    # --8<-- [end:callback]

    # --8<-- [start:draw]
    def draw(self):
        """The bar goes from the bottom of the frame up to value * height."""
        top = (HEIGHT - MARGIN) - self.value * (HEIGHT - 2 * MARGIN)
        self.canvas.coords(self.bar, MARGIN, top, WIDTH - MARGIN, HEIGHT - MARGIN)
    # --8<-- [end:draw]

    # --8<-- [start:loop]
    def tick(self):
        """Every 30 ms: let ROS deliver the messages that arrived, then redraw."""
        rclpy.spin_once(self, timeout_sec=0)
        self.draw()
        self.root.after(30, self.tick)

    def run(self):
        self.root.after(30, self.tick)
        self.root.mainloop()               # tkinter owns the main loop: ROS is served from tick()
    # --8<-- [end:loop]


def main():
    rclpy.init()
    gui = BarGui()
    try:
        gui.run()
    except KeyboardInterrupt:              # Ctrl+C in the terminal
        pass
    finally:
        gui.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
