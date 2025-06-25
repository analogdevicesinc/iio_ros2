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

import launch_ros
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from launch_testing.asserts import EXIT_OK
from rclpy.node import Node

import launch


@pytest.mark.launch_test
def generate_test_description():
    """Launch the node under test."""
    uri_arg = launch.actions.DeclareLaunchArgument(
        "uri",
        # default_value=['local:'],
        description='The URI of the IIO device to connect to',
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


class TestAdiIIONodeSmoke(unittest.TestCase):
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

    def test_node_starts(self, proc_output, proc_info, test_args):
        """Test if the node starts correctly."""
        self.node.get_logger().info(
            f"Waiting for node {test_args['node_name']} to become available..."
        )
        found = False
        start = time.time()
        while time.time() - start < 20.0 and not found:
            found = test_args["node_name"] in self.node.get_node_names()
            time.sleep(0.1)

        self.assertTrue(found), f"Node: {test_args['node_name']} not found!"
        self.node.get_logger().info(
            f"Node {test_args['node_name']} started successfully."
        )

    def test_services_available(self, proc_output, proc_info, test_args):
        """Test if the required services are available."""
        services = [
            "/ScanContext",
            "/AttrReadString",
            "/AttrWriteString",
            "/AttrEnableTopic",
            "/AttrDisableTopic",
            "/AttrDisableTopic",
            "/BufferRead",
            "/BufferWrite",
            "/BufferCreate",
            "/BufferDestroy",
            "/BufferRefill",
            "/BufferEnableTopic",
            "/BufferDisableTopic",
            "/ListDevices",
            "/ListChannels",
            "/ListAttributes",
            "/ScanContext",
        ]
        # Prefix the services with the node name
        services = [
            f"/{test_args['node_name']}{service}" for service in services]

        available_services = self.node.get_service_names_and_types()
        available_service_names = [srv[0] for srv in available_services]

        for service in services:
            found = service in available_service_names
            self.assertTrue(found), f"Service {service} not found!"

            self.node.get_logger().info(f"Service {service} is available.")


@launch_testing.post_shutdown_test()
class AdiIIONodeShutdown(unittest.TestCase):
    def test_exit_codes(self, proc_info):
        """Check if the processes exited normally."""
        launch_testing.asserts.assertExitCodes(
            proc_info, allowable_exit_codes=[EXIT_OK]
        )
