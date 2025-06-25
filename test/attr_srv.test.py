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

import random
import unittest

import launch_ros
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from adi_iio.srv import AttrReadString, AttrWriteString
from rclpy.node import Node

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


class TestAttrServices(unittest.TestCase):
    # Runs once when the test suite is started
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    # Runs before each test method
    def setUp(self):
        # Create a new ROS node to interact with the node under test
        self.node = Node("test_adi_iio_node")
        self.buffer = []

    # Runs before each test method
    def tearDown(self) -> None:
        self.node.destroy_node()

    def test_ctx_attr_read_string(self, proc_output, proc_info, test_args):
        """The /AttrReadString service should be available and return a string for a valid IIOPath."""
        attr_path = "uri"

        client = self.create_attr_read_string_client(test_args["node_name"])
        future = self.attr_read_string_request(client, attr_path)

        response: AttrReadString.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /AttrReadString failed: ")
        self.assertEqual(
            response.message,
            test_args["uri"],
            "Expected readback value to match the URI used to launch the node.",
        )

    def test_dev_attr_read_string(self, proc_output, proc_info, test_args):
        """The /AttrReadString service should be available and return a string for a valid IIOPath."""
        # TODO: change with a valid path on the target runner
        attr_path = "ad9361-phy/calib_mode"

        client = self.create_attr_read_string_client(test_args["node_name"])
        future = self.attr_read_string_request(client, attr_path)

        response: AttrReadString.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /AttrReadString failed: ")
        # Should check that the response.message contains a value
        self.assertTrue(
            response.message,
            f"Expected readback value to be non-empty for attribute path: {attr_path}",
        )

    def test_chn_attr_read_string(self, proc_output, proc_info, test_args):
        """The /AttrReadString service should be available and return a string for a valid IIOPath."""
        attr_path = "ad9361-phy/voltage0/gain_control_mode"

        client = self.create_attr_read_string_client(test_args["node_name"])
        future = self.attr_read_string_request(client, attr_path)

        response: AttrReadString.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /AttrReadString failed: ")
        # Should check that the response.message contains a value
        self.assertTrue(
            response.message,
            f"Expected readback value to be non-empty for attribute path: {attr_path}",
        )

    def test_invalid_attr_read_string_path(self, proc_output, proc_info, test_args):
        """The /AttrReadString service should be available but fail or an invalid IIOPath."""
        attr_path = "invalid"

        client = self.create_attr_read_string_client(test_args["node_name"])
        future = self.attr_read_string_request(client, attr_path)

        response: AttrReadString.Response = future.result()
        self.assertFalse(
            response.success,
            "Service call to /AttrReadString should have failed for invalid path"
        )

    def test_chn_attr_write_string(self, proc_output, proc_info, test_args):
        """The /AttrWriteString service should be available and write a string for a valid IIOPath."""
        attr_path = "ad9361-phy/altvoltage1/frequency"
        value = str(int(3e9))

        client = self.create_attr_write_string_client(test_args["node_name"])
        future = self.attr_write_string_request(client, attr_path, value)

        response: AttrWriteString.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /AttrWriteString failed: ")
        print(f"Response message: {response.message}")

        value = float(value)
        readback_value = float(response.message)
        self.assertAlmostEqual(
            readback_value,
            value,
            delta=value * 0.01,  # Allow 1% tolerance
            msg="Expected readback value to match the written value",
        )

    def test_attr_write_string_permission_denied(self, proc_output, proc_info, node, test_args):
        """The /AttrWriteString service should be available but fail for read-only attributes."""
        attr_path = "ad9361-phy/altvoltage1/frequency_available"
        value = str(int(3e9))

        client = self.create_attr_write_string_client(test_args["node_name"])
        future = self.attr_write_string_request(client, attr_path, value)

        response: AttrWriteString.Response = future.result()
        self.assertEqual(
            response.message,
            "Permission denied",
            "Expected write to read-only attribute to fail with 'Permission denied'",
        )
        self.assertFalse(
            response.success,
            "Service call to /AttrWriteString should have failed for read-only attribute",
        )

    def test_invalid_attr_write_string_path(self, proc_output, proc_info, test_args):
        """The /AttrWriteString service should be available but fail for invalid IIOPath."""
        attr_path = "invalid/iio/path"
        value = str(random.randint(4000, 4500))  # Valid fan speed values

        client = self.create_attr_write_string_client(test_args["node_name"])
        future = self.attr_write_string_request(client, attr_path, value)

        response = future.result()
        self.assertFalse(
            response.success,
            "Service call to /AttrWriteString should have failed for invalid path"
        )

    def test_rw_attr_string_loopback(self, proc_output, proc_info, test_args):
        """Test writing and reading back a string attribute."""
        attr_path = "ad9361-phy/altvoltage1/frequency"
        value = str(int(3e9))

        client_write = self.create_attr_write_string_client(
            test_args["node_name"])
        future = self.attr_write_string_request(client_write, attr_path, value)

        response: AttrWriteString.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /AttrWriteString failed: ")
        print(f"Response message: {response.message}")

        value = float(value)
        readback_value = float(response.message)
        self.assertAlmostEqual(
            readback_value,
            value,
            delta=value * 0.01,  # Allow 1% tolerance
            msg="Expected readback value to match the written value",
        )

        client_read = self.create_attr_read_string_client(
            test_args["node_name"])
        future = self.attr_read_string_request(client_read, attr_path)

        response: AttrReadString.Response = future.result()
        readback_value = float(response.message)
        self.assertTrue(response.success,
                        "Service call to /AttrReadString failed: ")
        self.assertAlmostEqual(
            readback_value,
            value,
            delta=value * 0.01,  # Allow 1% tolerance
            msg="Expected readback value to match the written value",
        )

    # Utility methods used by the tests

    def create_attr_read_string_client(self, node_name):
        """Create a client for the AttrReadString service."""
        client = self.node.create_client(
            AttrReadString, f"{node_name}/AttrReadString")
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /AttrReadString not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_attr_write_string_client(self, node_name):
        """Create a client for the AttrWriteString service."""
        client = self.node.create_client(
            AttrWriteString, f"{node_name}/AttrWriteString"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /AttrWriteString not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def attr_read_string_request(self, client, attr_path):
        """Create and send a request to the AttrReadString service."""
        request = AttrReadString.Request()
        request.attr_path = attr_path
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            f"Service call to /AttrReadString did not complete within {SRV_TIMEOUT} seconds.",
        )
        return future

    def attr_write_string_request(self, client, attr_path, value):
        """Create and send a request to the AttrWriteString service."""
        request = AttrWriteString.Request()
        request.attr_path = attr_path
        request.value = value
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            f"Service call to /AttrWriteString did not complete within {SRV_TIMEOUT} seconds.",
        )
        return future
