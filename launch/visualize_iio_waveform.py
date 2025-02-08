import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
import matplotlib.pyplot as plt
import argparse

class PlotNode(Node):
    def __init__(self, topic_name):
        super().__init__('plot_node')
        self.subscription = self.create_subscription(
            Int32MultiArray,
            topic_name,
            self.listener_callback,
            10
        )
        plt.ion()  # Interactive mode
        self.fig, self.ax = plt.subplots()

    def listener_callback(self, msg):
        
        m = msg.layout.dim[1].size  # Rows
        n = msg.layout.dim[0].size  # Columns

        data = msg.data

        if len(data) != m * n:
            self.get_logger().warn(f"Data size {len(data)} does not match expected {m}x{n}")
            return

        # Interleaved demuxing (column-major to row-major)
        matrix = [[0 for _ in range(n)] for _ in range(m)]
        for col in range(n):
            for row in range(m):
                index = row + col * m
                matrix[row][col] = data[index]

        #self.get_logger().info(f"Received matrix ({m}x{n}): {matrix}")

        # Plotting each row as a separate curve
        self.ax.clear()  # Clear previous plots
        for i, row in enumerate(matrix):
            self.ax.plot(range(n), row, label=f'Row {i + 1}')  # Plotting each row

        self.ax.set_title('Int32MultiArray Visualization')
        self.ax.set_xlabel('Column Index')
        self.ax.set_ylabel('Value')
        self.ax.legend()

        plt.draw()
        plt.pause(0.01)


def main():
    parser = argparse.ArgumentParser(description='Plot Int32MultiArray data from a ROS 2 topic.')
    parser.add_argument('--topic', type=str, required=True, help='ROS 2 topic to subscribe to')
    args = parser.parse_args()

    rclpy.init()
    node = PlotNode(args.topic)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()