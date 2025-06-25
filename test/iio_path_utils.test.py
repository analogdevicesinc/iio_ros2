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

import copy
import itertools
import unittest

import launch_ros
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from adi_iio.srv import ListAttributes, ListChannels, ListDevices, ScanContext
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


class TestIIOPathUtils(unittest.TestCase):
    """Validations for the IIO path utility services executed sequentially."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.device_paths = []
        cls.channel_paths = []
        cls.attr_paths = []
        cls.scan_ctx_response = None

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    # Runs before each test method
    def setUp(self):
        # Create a new ROS node to interact with the node under test
        self.node = Node("test_adi_iio_node")

    # Runs before each test method
    def tearDown(self) -> None:
        self.node.destroy_node()

    def test_00_list_devices(self, proc_output, proc_info, test_args):
        """
        /ListDevices service should be available and functional.

        The response should contain a list of IIO device paths.
        """
        client = self.node.create_client(
            ListDevices, f"/{test_args['node_name']}/ListDevices"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /ListDevices is not available within {SRV_TIMEOUT} seconds.",
        )

        request: ListDevices.Request = ListDevices.Request()
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            f"Service call to /ListDevices did not complete within {SRV_TIMEOUT} seconds.",
        )

        response: ListDevices.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /ListDevices failed.")
        self.node.get_logger().info(
            f"ListDevices response: {response.message}")

        TestIIOPathUtils.device_paths = copy.deepcopy(response.data)

    def test_01_list_channels(self, proc_output, proc_info, test_args):
        """
        /ListChannels service should be available and functional.

        The channels should be listed for each device returned by /ListDevices.
        """
        client = self.node.create_client(
            ListChannels, f"/{test_args['node_name']}/ListChannels"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /ListChannels is not available within {SRV_TIMEOUT} seconds.",
        )

        if not TestIIOPathUtils.device_paths:
            self.node.get_logger().warn("No devices found. Skipping ListChannels test.")
            return

        channels = []
        for device in TestIIOPathUtils.device_paths:
            request = ListChannels.Request()
            request.iio_path = device
            future = client.call_async(request)
            rclpy.spin_until_future_complete(
                self.node, future, timeout_sec=SRV_TIMEOUT)
            self.assertTrue(
                future.done(),
                f"Service call to /ListChannels for device {device} did not complete within {SRV_TIMEOUT} seconds.",
            )

            response: ListChannels.Response = future.result()
            self.assertTrue(
                response.success,
                f"Service call to /ListChannels for device {device} failed.",
            )
            self.node.get_logger().info(
                f"ListChannels response for {device}: {response.message}"
            )

            channels.extend(response.data)

        TestIIOPathUtils.channel_paths = copy.deepcopy(channels)
        self.node.get_logger().info(
            f"Total channels found: {len(TestIIOPathUtils.channel_paths)}"
        )

    def test_02_list_attributes(self, proc_output, proc_info, test_args):
        """
        /ListAttributes service should be available and functional.

        The attributes should be listed for each channel returned by /ListChannels.
        """
        client = self.node.create_client(
            ListAttributes, f"/{test_args['node_name']}/ListAttributes"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /ListAttributes is not available within {SRV_TIMEOUT} seconds.",
        )
        if not TestIIOPathUtils.channel_paths:
            self.node.get_logger().warn(
                "No channels found. Skipping ListAttributes test."
            )
            return
        attributes = []
        for iio_path in itertools.chain(
            TestIIOPathUtils.channel_paths,
            TestIIOPathUtils.device_paths,
            [""],  # IIOPath for context -> should return context attributes
        ):
            request = ListAttributes.Request()
            request.iio_path = iio_path
            future = client.call_async(request)
            rclpy.spin_until_future_complete(
                self.node, future, timeout_sec=SRV_TIMEOUT)
            self.assertTrue(
                future.done(),
                f"Service call to /ListAttributes for IIOPath {iio_path} did not complete within {SRV_TIMEOUT} seconds.",
            )

            response: ListAttributes.Response = future.result()
            self.assertTrue(
                response.success,
                f"Service call to /ListAttributes for channel {iio_path} failed.",
            )
            self.node.get_logger().info(
                f"ListAttributes response for {iio_path}: {response.message}"
            )

            attributes.extend(response.data)
        TestIIOPathUtils.attr_paths = copy.deepcopy(attributes)
        self.node.get_logger().info(
            f"Total attributes found: {len(TestIIOPathUtils.attr_paths)}"
        )

    def test_03_scan_context(self, proc_output, proc_info, test_args):
        """
        /ScanContext service should be available and functional.

        The return should be IIOPath for: Devices, Channels, Attributes.
        """
        client = self.node.create_client(
            ScanContext, f"/{test_args['node_name']}/ScanContext"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /ScanContext is not available within {SRV_TIMEOUT} seconds.",
        )
        request = ScanContext.Request()
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            f"Service call to /ScanContext did not complete within {SRV_TIMEOUT} seconds.",
        )

        response: ScanContext.Response = future.result()
        self.assertTrue(response.success,
                        "Service call to /ScanContext failed.")
        self.node.get_logger().info(
            f"ScanContext response: {response.message}")

        TestIIOPathUtils.scan_ctx_response = copy.deepcopy(response)

    def test_04_compare_results(self, proc_output, proc_info, test_args):
        """
        Compare the results of the previous methods to ensure consistency.

        The /ScanContext service results should correlate with the results obtained
        from /ListDevices, /ListChannels, and /ListAttributes services.
        """
        if not TestIIOPathUtils.scan_ctx_response:
            self.fail("ScanContext response is empty. Cannot compare results.")

        # Check devices
        for device_path in TestIIOPathUtils.device_paths:
            self.assertIn(
                device_path, TestIIOPathUtils.scan_ctx_response.devices)

        # Check channels
        for channel_path in TestIIOPathUtils.channel_paths:
            self.assertIn(
                channel_path, TestIIOPathUtils.scan_ctx_response.channels)

        # # Check attributes
        for attr_path in itertools.chain(
            TestIIOPathUtils.scan_ctx_response.context_attrs,
            TestIIOPathUtils.scan_ctx_response.device_attrs,
            TestIIOPathUtils.scan_ctx_response.channel_attrs,
        ):
            self.assertIn(attr_path, TestIIOPathUtils.attr_paths)
