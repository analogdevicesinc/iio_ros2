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

import time
import unittest
from typing import List

import launch_ros
import launch_ros.parameter_descriptions
import launch_testing
import launch_testing.actions
import numpy as np
import pytest
import rclpy
from adi_iio.srv import (AttrWriteString, BufferCreate, BufferDestroy,
                         BufferDisableTopic, BufferEnableTopic, BufferRead,
                         BufferRefill, BufferWrite)
from launch_testing_ros import WaitForTopics
from rclpy.node import Node
from scipy import signal
from std_msgs.msg import Int32MultiArray, MultiArrayDimension

import launch

SRV_TIMEOUT = 5.0  # [seconds]


@pytest.mark.launch_test
def generate_test_description():
    """Launch the node under test."""
    uri_arg = launch.actions.DeclareLaunchArgument(
        "uri",
        # default_value=['local:'],
        description="The URI of the IIO device to connect to",
    )
    node_name_arg = launch.actions.DeclareLaunchArgument(
        "node_name",
        # default_value=['adi_iio_node'],
        description="The name of the node to launch.",
    )
    timeout_arg = launch.actions.DeclareLaunchArgument(
        "timeout",
        default_value=["0"],
        description="Timeout for service calls in seconds.",
    )

    uri = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.LaunchConfiguration("uri"), value_type=str
    )
    node_name = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.LaunchConfiguration("node_name"), value_type=str
    )
    timeout = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.LaunchConfiguration("timeout"), value_type=int
    )

    adi_iio_node = launch_ros.actions.Node(
        package="adi_iio",
        executable="adi_iio_node",
        name=launch.substitutions.LaunchConfiguration("node_name"),
        parameters=[
            {
                "uri": uri,
                "node_name": node_name,
                "timeout": timeout,
            }
        ],
        # arguments=[
        #     "--ros-args",
        #     "--log-level",
        #     "debug",
        # ]
    )

    launch_description = launch.LaunchDescription()
    launch_description.add_action(uri_arg)
    launch_description.add_action(node_name_arg)
    launch_description.add_action(timeout_arg)
    launch_description.add_action(adi_iio_node)
    launch_description.add_action(launch_testing.actions.ReadyToTest())

    # Pass local parameters to each test
    test_context = {
        "node": adi_iio_node,
    }

    return launch_description, test_context


class TestBufferService(unittest.TestCase):
    """Test the buffer service."""

    # Runs once when the test suite is started
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = Node("test_adi_iio_node")
        self.buffer = []

    def tearDown(self) -> None:
        self.node.destroy_node()

    # ==========================================================================
    # /BufferCreate
    # ==========================================================================
    def test_buffer_create_srv_valid_device(self, proc_output, proc_info, test_args, node):
        """The /BufferCreate service should be available and functional."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 32,
        }
        self.execute_scenario_buffer_create(
            test_args,
            config=config,
            expected_success=True,
        )

        launch_testing.asserts.assertInStream(
            proc_output,
            str(config["samples_count"]),
            node
        )

    def test_buffer_create_srv_invalid_device(self, proc_output, proc_info, test_args, node):
        """The /BufferCreate service should handle invalid device paths gracefully."""
        config = {
            "device_path": "xadc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 32,
        }
        self.execute_scenario_buffer_create(
            test_args,
            config=config,
            expected_success=False,
        )

    # ==========================================================================
    # /BufferRefill
    # ==========================================================================
    def test_buffer_refill_srv_single_chn(self, proc_output, proc_info, test_args):
        """The /BufferRefill service should be available and functional."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0"],
            "samples_count": 32,
        }
        self.execute_scenario_buffer_create(
            test_args,
            config=config,
            expected_success=True,
        )

        for _ in range(10):
            self.execute_scenario_buffer_refill(
                test_args,
                config=config,
                expected_success=True,
            )

    def test_buffer_refill_srv_multiple_chn(self, proc_output, proc_info, test_args):
        """The /BufferRefill service should be available and functional."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 1024,
        }
        self.execute_scenario_buffer_create(
            test_args,
            config=config,
            expected_success=True,
        )

        for _ in range(10):
            self.execute_scenario_buffer_refill(
                test_args,
                config=config,
                expected_success=True,
            )

    # ==========================================================================
    # /BufferDestroy
    # ==========================================================================
    def test_buffer_destroy_srv_existing_buffer(self, proc_output, proc_info, test_args):
        """The /BufferDestroy service should be available and functional."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 32,
        }
        self.execute_scenario_buffer_create(
            test_args,
            config=config,
            expected_success=True,
        )

        # Should succeed only when a buffer exists
        self.execute_scenario_buffer_destroy(
            test_args,
            config=config,
            expected_success=True,
        )

        for _ in range(10):
            self.execute_scenario_buffer_destroy(
                test_args,
                config=config,
                expected_success=False,
            )

    # ==========================================================================
    # /BufferRead
    # ==========================================================================
    def test_buffer_read_valid_device(self, proc_output, proc_info, test_args):
        """The /BufferRead service should be available and functional."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 32,
        }

        self.execute_scenario_buffer_read(
            test_args,
            config=config,
            expected_success=True,
        )

    def test_buffer_read_srv_invalid_device(self, proc_output, proc_info, test_args):
        """The /BufferRead service should handle invalid device paths gracefully."""
        config = {
            "device_path": "xadc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 32,
        }

        self.execute_scenario_buffer_read(
            test_args,
            config=config,
            expected_success=False,
        )

    def test_buffer_read_srv_single_chn(self, proc_output, proc_info, test_args):
        """The /BufferRead service should be available and return the expected number of samples."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0"],
            "samples_count": 256,
        }

        for _ in range(10):
            self.execute_scenario_buffer_read(
                test_args,
                config=config,
                expected_success=True,
            )

    def test_buffer_read_srv_multiple_chn(self, proc_output, proc_info, test_args):
        """The /BufferRead service should be available and return the expected number of samples."""
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 1024,
        }

        for _ in range(10):
            self.execute_scenario_buffer_read(
                test_args,
                config=config,
                expected_success=True,
            )

    # ==========================================================================
    # /BufferWrite
    # ==========================================================================
    def test_buffer_write_invalid_device(self, proc_output, proc_info, test_args):
        """The /Buffer write should handle gracefully devices that are not buffer capable."""
        config = {
            "device_path": "ad9361-phy",  # NOT buffer capable
            "channels": ["output_voltage0"],
            "buffer": self.sine(
                samples_count=1024,
                amplitude=2 ** 14,
                phase=0
            ),
            "cyclic": True
        }

        self.execute_scenario_buffer_write(
            test_args,
            config=config,
            expected_success=False,
        )
        time.sleep(2)

    def test_buffer_write_single_chn(self, proc_output, proc_info, test_args):
        """The /BufferWrite service should be available and functional."""
        config = {
            "device_path": "cf-ad9361-dds-core-lpc",  # Buffer capable
            "channels": ["output_voltage0"],
            "buffer": self.sine(
                samples_count=1024,
                amplitude=2 ** 14,
                phase=0
            ),
            "cyclic": True
        }

        self.execute_scenario_buffer_write(
            test_args,
            config=config,
            expected_success=True,
        )
        time.sleep(2)

    def test_buffer_write_multiple_chn(self, proc_output, proc_info, test_args):
        """The /BufferWrite service should be available and functional."""
        buffer, data_sine, data_cosine = self.sine_cosine_interleaved(
            samples_count=1024,
            amplitude=2 ** 14,
            phase=0
        )

        config = {
            "device_path": "cf-ad9361-dds-core-lpc",
            "channels": ["voltage0", "output_voltage1"],
            "buffer": buffer,
            "cyclic": True
        }

        self.execute_scenario_buffer_write(
            test_args,
            config=config,
            expected_success=True,
        )
        time.sleep(2)

    # ==========================================================================
    # /BufferRead + /BufferWrite: Loopback
    # ==========================================================================
    def test_buffer_read_write_loopback(self, proc_output, proc_info, test_args):
        """Writes a cyclic buffer which is read back. Then compares the normalized buffers to validate they contain the same signal."""
        client_attr_write = self.create_attr_write_string_client(
            test_args["node_name"])
        self.attr_write_string_request(
            client_attr_write,
            attr_path="ad9361-phy/loopback",
            value="1"
        )

        # Write data
        samples_count = 1024
        buffer, write_sine, write_cosine = self.sine_cosine_interleaved(
            samples_count=samples_count,
            amplitude=2 ** 14,
            phase=0
        )
        config = {
            "device_path": "cf-ad9361-dds-core-lpc",
            "channels": ["voltage0", "voltage1"],
            "buffer": buffer,
            "samples_count": samples_count,
            "cyclic": True
        }

        response = self.execute_scenario_buffer_write(
            test_args,
            config=config,
            expected_success=True,
        )
        time.sleep(1)

        # Read Data
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": samples_count,
        }
        for _ in range(10):
            response = self.execute_scenario_buffer_read(
                test_args,
                config=config,
                expected_success=True,
            )

            read_buffer = np.array(response.buffer.data)
            read_sine, read_cosine = self.deinterleave_data(read_buffer)

            # Preprocess: normalize data
            write_sine_norm = write_sine / np.max(np.abs(write_sine))
            write_cosine_norm = write_cosine / np.max(np.abs(write_cosine))
            read_sine_norm = read_sine / np.max(np.abs(read_sine))
            read_cosine_norm = read_cosine / np.max(np.abs(read_cosine))

            # Preprocess: align the read signals to the written ones
            offset_sine, max_corr_sine = self.align_and_correlate(
                write_sine_norm, read_sine_norm)

            read_sine_norm = np.roll(read_sine_norm, offset_sine)
            offset_cosine, max_corr_cosine = self.align_and_correlate(
                write_cosine_norm, read_cosine_norm)
            read_cosine_norm = np.roll(read_cosine_norm, offset_cosine)

            # Validation: check if the read signals are similar to the written ones
            self.assertGreaterEqual(
                # Handle inverted signal after alignment
                np.abs(max_corr_sine),
                0.75,
                f"Sine wave readback correlation too low: {max_corr_sine:.4f}"
            )
            self.assertGreaterEqual(
                # Handle inverted signal after alignment
                np.abs(max_corr_cosine),
                0.75,
                f"Cosine wave readback correlation too low: {max_corr_cosine:.4f}"
            )

    # ==========================================================================
    # /BufferEnableTopic + /BufferDisableTopic
    # ==========================================================================
    def test_buffer_enable_topic(self, proc_output, proc_info, test_args):
        # Setup debug mode
        client_attr_write = self.create_attr_write_string_client(
            test_args["node_name"])
        self.attr_write_string_request(
            client_attr_write,
            attr_path="ad9361-phy/loopback",
            value="1"
        )

        # Write data
        samples_count = 1024
        amplitude = 2**14
        buffer, write_sine, write_cosine = self.sine_cosine_interleaved(
            samples_count=samples_count,
            amplitude=amplitude,
            phase=0
        )
        config = {
            "device_path": "cf-ad9361-dds-core-lpc",
            "channels": ["voltage0", "voltage1"],
            "buffer": buffer,
            "samples_count": samples_count,
            "cyclic": True
        }

        self.execute_scenario_buffer_write(
            test_args,
            config=config,
            expected_success=True,
        )

        # Create buffer
        config = {
            "device_path": "cf-ad9361-lpc",
            "channels": ["voltage0", "voltage1"],
            "samples_count": 256,
            "topic_name": "/cf_ad9361_lpc",
            "loop_rate": 1.0,
            # Topic validation config
            "buffer_length": 500,  # number of messages to receive from the topic
            "time_window": 10.0,  # how long to listen for data within the topic
            "tolerance": 0.9  # difference tolerance for the loop rate validation
        }
        self.execute_scenario_buffer_create(
            test_args,
            config=config,
            expected_success=True,
        )

        # Stream buffer to topic
        self.execute_scenario_buffer_enable_topic(
            test_args,
            config=config,
            expected_success=True
        )
        # Validate topic creation
        topic_names = [val[0] for val in self.node.get_topic_names_and_types()]
        self.assertIn(
            config["topic_name"],
            topic_names,
            f"Topic {config['topic_name']} not found in the list of topics: {topic_names}",
        )
        # Validate topic loop_rate
        expected_topic_list = [(config["topic_name"], Int32MultiArray)]
        time_start = time.time()
        with WaitForTopics(
            expected_topic_list,
            timeout=SRV_TIMEOUT,
            messages_received_buffer_length=config["buffer_length"]
        ) as wait_for_topics:
            time.sleep(config["time_window"])
            time_end = time.time()
            elapsed_time = time_end - time_start

            received_messages = wait_for_topics.received_messages(
                config["topic_name"])

            # Validate message count and rate
            estimated_loop_rate = len(received_messages) / elapsed_time
            expected_rate = config["loop_rate"]
            tolerance = config["tolerance"] * expected_rate

            self.assertAlmostEqual(
                estimated_loop_rate,
                expected_rate,
                delta=tolerance,
                msg=f"Loop Rate validation failed; Expected: {expected_rate}Hz, Got: {estimated_loop_rate:.2f}Hz"
            )

            for msg in received_messages:
                data = msg.data
                signal1, signal2 = self.deinterleave_data(data)
                signal1 = np.array(signal1)
                signal2 = np.array(signal2)

                self.assertEqual(
                    len(signal1),
                    config["samples_count"],
                    msg=f"Signal1: Expected {config['samples_count']} samples, got {len(signal1)}"
                )
                self.assertTrue(
                    np.any(np.abs(signal1) > 500),
                    msg="Signal1 should contain samples from the written buffer, not just noise."
                )

                self.assertEqual(
                    len(signal2),
                    config["samples_count"],
                    msg=f"Signal2: Expected {config['samples_count']} samples, got {len(signal2)}"
                )
                self.assertTrue(
                    np.any(np.abs(signal2) > 500),
                    msg="Signal2 should contain samples from the written buffer, not just noise."
                )

        self.execute_scenario_buffer_disable_topic(
            test_args,
            config=config,
            expected_success=True
        )
        time.sleep(4)
        # Validate topic was disabled
        topic_names = [val[0] for val in self.node.get_topic_names_and_types()]
        self.assertNotIn(
            config["topic_name"],
            topic_names,
            f"Topic {config['topic_name']} not found in the list of topics: {topic_names}",
        )

    # ==========================================================================
    # Parameterized test scenarios
    # ==========================================================================

    def execute_scenario_buffer_create(self, test_args, config, expected_success):
        client_create = self.create_buffer_create_client(
            test_args["node_name"])
        future = self.buffer_create_request(
            client_create,
            device_path=config["device_path"],
            channels=config["channels"],
            samples_count=config["samples_count"],
        )

        response: BufferCreate.Response = future.result()
        if expected_success:
            self.assertTrue(
                response.success,
                "BufferCreate service call failed: " + response.message,
            )
        else:
            self.assertFalse(
                response.success,
                "BufferCreate service call should have failed but succeeded.",
            )
        return response

    def execute_scenario_buffer_refill(self, test_args, config, expected_success):
        client_refill = self.create_buffer_refill_client(
            test_args["node_name"])
        future = self.buffer_refill_request(
            client_refill,
            device_path=config["device_path"],
        )
        response: BufferRefill.Response = future.result()
        if expected_success:
            self.assertTrue(
                response.success,
                "BufferRefill service call failed: " + response.message,
            )
            self.assertEqual(
                int(len(response.buffer.data)),
                int(config["samples_count"]) * len(config["channels"]),
                "BufferRefill did not return the expected number of samples.",
            )
        else:
            self.assertFalse(
                response.success,
                "BufferRefill service call should have failed but succeeded.",
            )
        return response

    def execute_scenario_buffer_destroy(self, test_args, config, expected_success):
        client_destroy = self.create_buffer_destroy_client(
            test_args["node_name"])
        future = self.buffer_destroy_request(
            client_destroy,
            device_path=config["device_path"],
        )

        response: BufferDestroy.Response = future.result()

        if expected_success:
            self.assertTrue(
                response.success,
                "BufferDestroy service call failed: " + response.message,
            )
        else:
            self.assertFalse(
                response.success,
                "BufferDestroy service call should have failed but succeeded.",
            )
        return response

    def execute_scenario_buffer_read(self, test_args, config, expected_success):
        client_read = self.create_buffer_read_client(test_args["node_name"])
        future = self.buffer_read_request(
            client_read,
            device_path=config["device_path"],
            channels=config["channels"],
            samples_count=config["samples_count"],
        )

        response: BufferRead.Response = future.result()

        if expected_success:
            self.assertTrue(
                response.success,
                "BufferRead service call failed: " + response.message,
            )
            self.assertEqual(
                int(len(response.buffer.data)),
                int(config["samples_count"]) * len(config["channels"]),
                "BufferRead did not return the expected number of samples.",
            )
        else:
            self.assertFalse(
                response.success,
                "BufferRead service call should have failed but succeeded.",
            )
            self.assertEqual(
                len(response.buffer.data),
                0,
                "BufferRead should return an empty buffer on failure.",
            )
        return response

    def execute_scenario_buffer_write(self, test_args, config, expected_success):
        client_write = self.create_buffer_write_client(test_args["node_name"])
        future = self.buffer_write_request(
            client_write,
            device_path=config["device_path"],
            channels=config["channels"],
            buffer=config["buffer"],
            cyclic=config["cyclic"],
        )

        response: BufferWrite.Response = future.result()

        if expected_success:
            self.assertTrue(
                response.success,
                "BufferWrite service call failed: " + response.message,
            )
        else:
            self.assertFalse(
                response.success,
                "BufferWrite service call should have failed but succeeded.",
            )
        return response

    def execute_scenario_buffer_enable_topic(self, test_args, config, expected_success):
        client_buffer_enable_topic = self.create_buffer_enable_topic_client(
            test_args["node_name"]
        )
        future = self.buffer_enable_topic_request(
            client_buffer_enable_topic,
            device_path=config["device_path"],
            topic_name=config["topic_name"],
            loop_rate=config["loop_rate"],
        )

        response: BufferEnableTopic.Response = future.result()

        if expected_success:
            self.assertTrue(
                response.success,
                "BufferEnableTopic service call failed: " + response.message,
            )
        else:
            self.assertFalse(
                response.success,
                "BufferEnableTopic service call should have failed but succeeded.",
            )
        return response

    def execute_scenario_buffer_disable_topic(self, test_args, config, expected_success):
        client_buffer_disable_topic = self.create_buffer_disable_topic_client(
            test_args["node_name"]
        )
        future = self.buffer_disable_topic_request(
            client_buffer_disable_topic,
            device_path=config["device_path"],
        )
        response: BufferDisableTopic.Response = future.result()

        if expected_success:
            self.assertTrue(
                response.success,
                "BufferDisableTopic service call failed: " + response.message,
            )
        else:
            self.assertFalse(
                response.success,
                "BufferDisableTopic service call should have failed but succeeded.",
            )
        return response

    # ==========================================================================
    # Utility methods
    # ==========================================================================

    def create_buffer_create_client(self, node_name):
        """Create a client for the BufferCreate service."""
        client = self.node.create_client(
            BufferCreate, f"{node_name}/BufferCreate")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferCreate not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_buffer_destroy_client(self, node_name):
        """Create a client for the BufferDestroy service."""
        client = self.node.create_client(
            BufferDestroy, f"{node_name}/BufferDestroy")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferDestroy not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_buffer_enable_topic_client(self, node_name):
        """Create a client for the BufferEnableTopic service."""
        client = self.node.create_client(
            BufferEnableTopic, f"{node_name}/BufferEnableTopic"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferEnableTopic not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_buffer_disable_topic_client(self, node_name):
        """Create a client for the BufferDisableTopic service."""
        client = self.node.create_client(
            BufferDisableTopic, f"{node_name}/BufferDisableTopic"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferDisableTopic not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_buffer_read_client(self, node_name):
        """Create a client for the BufferRead service."""
        client = self.node.create_client(BufferRead, f"{node_name}/BufferRead")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferRead not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_buffer_refill_client(self, node_name):
        """Create a client for the BufferRefill service."""
        client = self.node.create_client(
            BufferRefill, f"{node_name}/BufferRefill")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferRefill not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_buffer_write_client(self, node_name):
        """Create a client for the BufferWrite service."""
        client = self.node.create_client(
            BufferWrite, f"{node_name}/BufferWrite")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /BufferWrite not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_attr_write_string_client(self, node_name):
        """Create a client for the /AttrWriteString service."""
        client = self.node.create_client(
            AttrWriteString, f"{node_name}/AttrWriteString")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /AttrWriteString not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def buffer_create_request(
        self, client, device_path: str, channels: List[str], samples_count: int
    ):
        """Create a request for the BufferCreate service."""
        request = BufferCreate.Request()
        request.device_path = device_path
        request.channels = channels
        request.samples_count = samples_count
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            "BufferCreate service call did not complete within the timeout.",
        )
        return future

    def buffer_refill_request(self, client, device_path: str):
        """Create a request for the BufferRefill service."""
        request = BufferRefill.Request()
        request.device_path = device_path
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            "BufferRefill service call did not complete within the timeout.",
        )
        return future

    def buffer_destroy_request(self, client, device_path: str):
        """Create a request for the BufferDestroy service."""
        request = BufferDestroy.Request()
        request.device_path = device_path
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            "BufferDestroy service call did not complete within the timeout.",
        )
        return future

    def buffer_read_request(self, client, device_path: str, channels: List[str], samples_count: int):
        """Create a request for the BufferRead service."""
        request = BufferRead.Request()
        request.device_path = device_path
        request.channels = channels
        request.samples_count = samples_count
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            "BufferRead service call did not complete within the timeout.",
        )
        return future

    def buffer_write_request(
        self,
        client,
        device_path: str,
        channels: List[str],
        buffer: Int32MultiArray,
        cyclic: bool
    ):
        """Create a request for the BufferWrite service."""
        request = BufferWrite.Request()
        request.device_path = device_path
        request.channels = channels
        request.buffer = buffer
        request.cyclic = cyclic
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=SRV_TIMEOUT
                                         )
        self.assertTrue(
            future.done(),
            "BufferWrite service call did not complete within the timeout.",
        )
        return future

    def buffer_enable_topic_request(
        self,
        client,
        device_path: str,
        topic_name: str,
        loop_rate: float
    ):
        """Create a request for the BufferEnableTopic service."""
        request = BufferEnableTopic.Request()
        request.device_path = device_path
        request.topic_name = topic_name
        request.loop_rate = loop_rate
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=SRV_TIMEOUT
                                         )
        self.assertTrue(
            future.done(),
            "BufferEnableTopic service call did not complete within the timeout.",
        )
        return future

    def buffer_disable_topic_request(
        self,
        client,
        device_path: str,
    ):
        """Create a request for the BufferDisableTopic service."""
        request = BufferDisableTopic.Request()
        request.device_path = device_path
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=SRV_TIMEOUT
                                         )
        self.assertTrue(
            future.done(),
            "BufferDisableTopic service call did not complete within the timeout.",
        )
        return future

    def attr_write_string_request(self, client, attr_path: str, value: str):
        """Create a request for the AttrWriteString service."""
        request = AttrWriteString.Request()
        request.attr_path = attr_path
        request.value = value
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            "AttrWriteString service call did not complete within the timeout.",
        )
        return future

    def sine(self, samples_count: int, amplitude: int, phase: float = 0):
        data = np.sin(np.linspace(0, 2 * np.pi + phase,
                      samples_count)) * amplitude

        data = data.astype(int)

        buffer: Int32MultiArray = Int32MultiArray()
        buffer.layout.dim.append(MultiArrayDimension(
            label="samples",
            size=len(data),
            stride=len(data) * 1  # Assuming each sample is an Int32
        ))
        buffer.layout.dim.append(MultiArrayDimension(
            label="channels",
            size=1,
            stride=1
        ))
        buffer.layout.data_offset = 0
        buffer.data = data.tolist()

        return buffer

    def sine_cosine_interleaved(self, samples_count: int, amplitude: int, phase: float = 0):
        t = np.linspace(0, 2 * np.pi, samples_count)
        data_sine = np.sin(t + phase) * amplitude
        data_sine = data_sine.astype(int)
        data_cosine = np.sin(t + np.pi / 2 + phase) * amplitude
        data_cosine = data_cosine.astype(int)

        data_interleaved = self.interleave_data(data_sine, data_cosine)

        buffer: Int32MultiArray = Int32MultiArray()
        buffer.layout.dim.append(MultiArrayDimension(
            label="samples",
            size=samples_count,
            stride=samples_count * 2  # 2 channels
        ))
        buffer.layout.dim.append(MultiArrayDimension(
            label="channels",
            size=2,
            stride=2
        ))
        buffer.layout.data_offset = 0
        buffer.data = data_interleaved.tolist()

        return buffer, data_sine, data_cosine

    def interleave_data(self, buffer1, buffer2):
        if len(buffer1) != len(buffer2):
            print("Error: Buffers must be of the same length")
            return None

        interleaved = []
        for i in range(len(buffer1)):
            interleaved.append(buffer1[i])
            interleaved.append(buffer2[i])

        return np.array(interleaved)

    def deinterleave_data(self, data):
        if len(data) % 2 != 0:
            print("Error: Interleaved data must have an even length")
            return None

        buffer1 = data[::2]
        buffer2 = data[1::2]

        return buffer1, buffer2

    def align_and_correlate(self, signal1, signal2):
        """Aligns input signals using cross-correlation."""
        correlation = signal.correlate(
            signal1, signal2, mode='full', method='auto')
        # Normalize to [-1;1]
        correlation /= np.sqrt(np.sum(np.abs(signal2)**2)
                               * np.sum(np.abs(signal1)**2))
        lags = signal.correlation_lags(signal1.size, signal2.size, mode='full')

        # Find the index of the peak correlation
        # Use abs for magnitude of correlation
        peak_idx = np.argmax(np.abs(correlation))
        offset_samples = lags[peak_idx]
        # This is the correlation value at optimal alignment
        max_correlation_value = correlation[peak_idx]

        return offset_samples, max_correlation_value
