# Copyright 2025 Analog Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class StateMachine(Node):
    SCALE_VALUE = 0.610351562
    N_POINTS = 1024
    SIGNAL = np.linspace(0, 2.5, N_POINTS)

    STATE_TRANSITIONS = {
        "ANODE_RISING": {"next": "ANODE_FALLING", "increment": 1, "target_idx": N_POINTS - 1},
        "ANODE_FALLING": {"next": "CATHODE_RISING", "increment": -1, "target_idx": 0},
        "CATHODE_RISING": {"next": "CATHODE_FALLING", "increment": 1, "target_idx": N_POINTS - 1},
        "CATHODE_FALLING": {"next": "ANODE_RISING", "increment": -1, "target_idx": 0}
    }

    def __init__(self):
        super().__init__('state')

        n_states = len(list(self.STATE_TRANSITIONS.keys()))

        self.declare_parameter('state_period', 1.0)
        self.declare_parameter("anode_topic", "anode")
        self.declare_parameter("cathode_topic", "cathode")

        self.state_period = self.get_parameter('state_period').value
        self.anode_topic = self.get_parameter("anode_topic").value
        self.cathode_topic = self.get_parameter("cathode_topic").value

        self.update_rate = self.state_period / (self.N_POINTS * n_states)

        self.state = list(self.STATE_TRANSITIONS.keys())[0]
        self.idx = 0

        self.get_logger().info(f'Number of states: {n_states}')
        self.get_logger().info(f'State period: {self.state_period} [s]')
        self.get_logger().info(f"Anode topic: {self.anode_topic}")
        self.get_logger().info(f"Cathode topic: {self.cathode_topic}")

        self.publisher_anode = self.create_publisher(
            Float64, self.anode_topic, 10)
        self.publisher_cathode = self.create_publisher(
            Float64, self.cathode_topic, 10)

        self.timer = self.create_timer(self.update_rate, self.timer_callback)

    def timer_callback(self):
        msg = Float64()
        volts = self.SIGNAL[self.idx]
        # mV = self.SIGNAL[self.idx] * 1_000
        # raw_value = int(mV / self.SCALE_VALUE)
        msg.data = volts

        if self.state.startswith("ANODE"):
            self.get_logger().debug(f'{self.state}: {volts} [V]')
            self.publisher_anode.publish(msg)
        elif self.state.startswith("CATHODE"):
            self.get_logger().debug(f'{self.state}: {volts} [V]')
            self.publisher_cathode.publish(msg)
        else:
            self.get_logger().error(f'Invalid state: {self.state}')
            self.state = "ANODE_RISING"  # Reset to a valid state

        self.update_state()

    def update_state(self):
        if self.state not in self.STATE_TRANSITIONS:
            self.get_logger().error(
                f'Invalid state: {self.state}. Resetting to ANODE_RISING')
            self.state = "ANODE_RISING"
            return

        transition = self.STATE_TRANSITIONS[self.state]

        self.idx = (self.idx + transition["increment"]) % self.N_POINTS

        # Check if transition condition is met
        if self.idx == transition["target_idx"]:
            self.state = transition["next"]


def main(args=None):
    rclpy.init(args=args)
    node = StateMachine()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Signal generation stopped by user')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
