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
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

import adi_iio
import adi_iio.srv
import launch_ros
import launch_ros.parameter_descriptions
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from adi_iio.srv import AttrDisableTopic, AttrEnableTopic
from launch_testing_ros import WaitForTopics
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Int32, String

import launch

SRV_TIMEOUT = 5.0  # [seconds]


class TopicType(Enum):
    """Enum for topic data types."""

    STRING = adi_iio.srv.AttrEnableTopic.Request.STRING
    INT32 = adi_iio.srv.AttrEnableTopic.Request.INT
    FLOAT32 = adi_iio.srv.AttrEnableTopic.Request.DOUBLE
    BOOL = adi_iio.srv.AttrEnableTopic.Request.BOOL


@dataclass
class EnableTopicConfiguration:
    """Configuration for enabling an attribute topic."""

    attr_path: str
    topic_name: str = ""
    loop_rate: float = 10.0
    topic_type: TopicType = TopicType.STRING

    # Expected outcomes
    expected_success: bool = True

    # Validation parameters
    validate_topic_creation: bool = True
    validate_data_flow: bool = True
    time_window: float = 5.0
    rate_tolerance: float = 0.05  # 5% tolerance
    buffer_length: int = 500

    # Test behavior
    description: str = ""
    should_skip: bool = False
    skip_reason: str = ""

    def __post_init__(self):
        """Set defaults based on configuration."""
        if not self.description:
            self.description = f"Enable {self.attr_path} as {self.topic_type.name} at {self.loop_rate}Hz"

    @property
    def expected_topics(self) -> List[str]:
        """Generate expected topic names."""
        prefix = self.topic_name if self.topic_name else self.attr_path.replace(
            '-', '_')
        if not prefix.startswith('/'):
            prefix = f"/{prefix}"
        return [f"{prefix}/read", f"{prefix}/write"]

    @property
    def expected_msg_type(self) -> str:
        """Get expected message type string."""
        type_mapping = {
            TopicType.STRING: "std_msgs/msg/String",
            TopicType.INT32: "std_msgs/msg/Int32",
            TopicType.FLOAT32: "std_msgs/msg/Float32",
            TopicType.BOOL: "std_msgs/msg/Bool"
        }
        return type_mapping[self.topic_type]


@dataclass
class DisableTopicConfiguration:
    """Configuration for disabling an attribute topic."""

    topic_name: str
    topic_type: TopicType = TopicType.STRING

    # Expected outcomes
    expected_success: bool = True

    # Validation parameters
    validate_topic_removal: bool = True

    # Test behavior
    description: str = ""
    should_skip: bool = False
    skip_reason: str = ""

    def __post_init__(self):
        """Set defaults based on configuration."""
        if not self.description:
            self.description = f"Disable topic {self.topic_name} ({self.topic_type.name})"


@dataclass
class TestScenario:
    """Complete test scenario that chains enable and disable operations."""

    name: str
    description: str
    enable_configs: List[EnableTopicConfiguration]
    disable_configs: List[DisableTopicConfiguration]

    # Global test behavior
    should_skip: bool = False
    skip_reason: str = ""

    def __post_init__(self):
        """Validate configuration."""
        if not self.enable_configs:
            raise ValueError(
                "Test scenario must have at least one enable configuration")


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
        # arguments=["--ros-args", "--log-level", "debug",]
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


class TestAttrTopicServices(unittest.TestCase):
    """Parameterized test class for attribute topic services."""

    # Test scenarios with chained enable/disable operations
    TEST_SCENARIOS = [
        TestScenario(
            name="basic_string_topic",
            description="Basic string topic enable/disable cycle",
            enable_configs=[
                EnableTopicConfiguration(
                    attr_path="xadc/voltage0/raw",
                    topic_name="",
                    loop_rate=10.0,
                    topic_type=TopicType.STRING,
                )
            ],
            disable_configs=[
                # TODO: tbd - disable only uses the topic name as ID, type is not used!!
                DisableTopicConfiguration(
                    topic_name="xadc/voltage0/raw",
                    topic_type=TopicType.STRING,
                    expected_success=True,
                    description="Disable raw input topic"
                ),
                DisableTopicConfiguration(
                    topic_name="xadc/voltage0/raw",
                    topic_type=TopicType.STRING,
                    expected_success=False,
                    description="Attempt to disable an already disabled raw input topic",
                )
            ]
        ),

        TestScenario(
            name="multiple_topics_mixed_success",
            description="Enable multiple topics, then disable with mixed success/failure",
            enable_configs=[
                EnableTopicConfiguration(
                    attr_path="xadc/voltage0/raw",
                    topic_name="raw0",
                    loop_rate=5.0,
                    topic_type=TopicType.STRING
                ),
                EnableTopicConfiguration(
                    attr_path="xadc/voltage1/raw",
                    topic_name="raw1",
                    loop_rate=2.0,
                    topic_type=TopicType.INT32
                )
            ],
            disable_configs=[
                DisableTopicConfiguration(
                    topic_name="raw0",
                    topic_type=TopicType.STRING,
                    expected_success=True,
                    description="Should successfully disable fan1 topic"
                ),
                DisableTopicConfiguration(
                    topic_name="nonexistent_topic",
                    topic_type=TopicType.STRING,
                    expected_success=False,
                    description="Should fail to disable non-existent topic"
                ),
                DisableTopicConfiguration(
                    topic_name="raw1",
                    topic_type=TopicType.INT32,
                    expected_success=True,
                    description="Should successfully disable GPU frequency topic"
                )
            ]
        ),

        TestScenario(
            name="invalid_enable_followed_by_cleanup",
            description="Try invalid enable, then cleanup operations",
            enable_configs=[
                EnableTopicConfiguration(
                    attr_path="invalid/path/test",
                    topic_name="invalid_topic",
                    expected_success=False,
                    validate_topic_creation=False,
                    validate_data_flow=False,
                    description="Should fail to enable invalid path"
                )
            ],
            disable_configs=[
                DisableTopicConfiguration(
                    topic_name="invalid_topic",
                    topic_type=TopicType.STRING,
                    expected_success=False,
                    validate_topic_removal=False,
                    description="Should fail to disable topic that was never created"
                )
            ]
        ),

        TestScenario(
            name="high_frequency_float_test",
            description="High frequency float topic with proper cleanup",
            enable_configs=[
                EnableTopicConfiguration(
                    attr_path="xadc/voltage0/raw",
                    topic_name="raw0",
                    loop_rate=80.0,
                    topic_type=TopicType.FLOAT32,
                    time_window=3.0,  # Shorter validation window for high freq
                    description="High frequency accelerometer scale"
                )
            ],
            disable_configs=[
                DisableTopicConfiguration(
                    topic_name="raw0",
                    topic_type=TopicType.FLOAT32,
                    description="Clean up high frequency topic"
                )
            ]
        )
    ]

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

    def execute_test_scenario(self, scenario: TestScenario, test_args: Dict[str, Any]):
        """Execute a complete test scenario with chained enable(1)/disable(1+) operations."""
        if scenario.should_skip:
            self.skipTest(scenario.skip_reason)

        self.node.get_logger().info(
            f"Starting scenario: {scenario.name} - {scenario.description}")

        # Execute all enable operations
        for enable_config in scenario.enable_configs:
            self.node.get_logger().info(
                f"Executing enable: {enable_config.description}")
            self.execute_enable_topic_test(enable_config, test_args)

        # Execute all disable operations
        for disable_config in scenario.disable_configs:
            self.node.get_logger().info(
                f"Executing disable: {disable_config.description}")
            self.execute_disable_topic_test(disable_config, test_args)

        self.node.get_logger().info(f"Completed scenario: {scenario.name}")

    def execute_enable_topic_test(self, config: EnableTopicConfiguration, test_args: Dict[str, Any]):
        """Execute an enable topic test with the given configuration."""
        # Skip test if configured
        if config.should_skip:
            self.skipTest(config.skip_reason)

        client = self.create_attr_enable_topic_client(test_args["node_name"])
        future = self.attr_enable_topic_request(
            client=client,
            attr_path=config.attr_path,
            topic_name=config.topic_name,
            loop_rate=config.loop_rate,
            type=config.topic_type.value
        )

        response: AttrEnableTopic.Response = future.result()

        # Validate response success/failure
        if config.expected_success:
            self.assertTrue(
                response.success,
                f"Service call failed for {config.description}: {response.message}"
            )

            # Only do validation if the enable was expected to succeed
            if config.validate_topic_creation:
                self._validate_topic_creation(config)

            if config.validate_data_flow:
                self._validate_topic_data_and_rate(config)
        else:
            self.assertFalse(
                response.success,
                f"Service call should have failed for {config.description}"
            )

    def execute_disable_topic_test(self, config: DisableTopicConfiguration, test_args: Dict[str, Any]):
        """Execute a disable topic test with the given configuration."""
        if config.should_skip:
            self.skipTest(config.skip_reason)

        client = self.create_attr_disable_topic_client(test_args["node_name"])
        future = self.attr_disable_topic_request(
            client=client,
            topic_name=config.topic_name,
            type=config.topic_type.value
        )

        response: AttrDisableTopic.Response = future.result()

        # Validate response success/failure
        if config.expected_success:
            self.assertTrue(
                response.success,
                f"Disable operation failed for {config.description}: {response.message}"
            )
        else:
            self.assertFalse(
                response.success,
                f"Disable operation should have failed for {config.description}"
            )

        # Validate topic removal if requested
        if config.validate_topic_removal and config.expected_success:
            self._validate_topic_removed(config)

    def _validate_topic_creation(self, config: EnableTopicConfiguration):
        """Validate that expected topics are created with correct types."""
        for expected_topic in config.expected_topics:
            topic_found = False
            type_correct = False

            for topic_name, topic_types in self.node.get_topic_names_and_types():
                if topic_name == expected_topic:
                    topic_found = True
                    if config.expected_msg_type in topic_types:
                        type_correct = True
                    break

            self.assertTrue(
                topic_found,
                f"Expected topic {expected_topic} not found for {config.description}"
            )
            self.assertTrue(
                type_correct,
                f"Expected topic {expected_topic} has wrong type. Expected {config.expected_msg_type}"
            )

    def _validate_topic_removed(self, config: DisableTopicConfiguration):
        """Validate that topic has been removed."""
        time.sleep(0.5)  # small delay to allow Topic removal to propagate
        topic_names = [name for name,
                       _ in self.node.get_topic_names_and_types()]
        for topic_name in topic_names:
            self.assertFalse(
                topic_name.startswith(config.topic_name),
                f"Topic {topic_name} should have been removed after disabling {config.topic_name}"
            )

    def _validate_topic_data_and_rate(self, config: EnableTopicConfiguration):
        """Validate topic data flow and publishing rate."""
        # Get message type class
        msg_type_mapping = {
            TopicType.STRING: String,
            TopicType.INT32: Int32,
            TopicType.FLOAT32: Float32,
            TopicType.BOOL: Bool
        }
        msg_class = msg_type_mapping[config.topic_type]

        # Test only the read topic for rate validation
        read_topic = config.expected_topics[0]  # Assuming first is read topic
        expected_topic_list = [(read_topic, msg_class)]

        time_start = time.time()
        with WaitForTopics(
            expected_topic_list,
            timeout=SRV_TIMEOUT,
            messages_received_buffer_length=config.buffer_length
        ) as wait_for_topics:
            time.sleep(config.time_window)
            time_end = time.time()
            elapsed_time = time_end - time_start

            received_messages = wait_for_topics.received_messages(read_topic)

            # Validate message count and rate
            estimated_loop_rate = len(received_messages) / elapsed_time
            expected_rate = config.loop_rate
            tolerance = config.rate_tolerance * expected_rate

            self.assertAlmostEqual(
                estimated_loop_rate,
                expected_rate,
                delta=tolerance,
                msg=f"Rate validation failed for {config.description}. "
                    f"Expected: {expected_rate}Hz, Got: {estimated_loop_rate:.2f}Hz"
            )

    # Generate individual test methods for each scenario
    def test_basic_string_topic_scenario(self, proc_output, proc_info, test_args):
        """Test basic string topic enable/disable cycle."""
        scenario = self.TEST_SCENARIOS[0]
        self.execute_test_scenario(scenario, test_args)

    def test_multiple_topics_mixed_success_scenario(self, proc_output, proc_info, test_args):
        """Test multiple topics with mixed success/failure disable operations."""
        scenario = self.TEST_SCENARIOS[1]
        self.execute_test_scenario(scenario, test_args)

    def test_invalid_enable_followed_by_cleanup_scenario(self, proc_output, proc_info, test_args):
        """Test invalid enable followed by cleanup operations."""
        scenario = self.TEST_SCENARIOS[2]
        self.execute_test_scenario(scenario, test_args)

    def test_high_frequency_float_scenario(self, proc_output, proc_info, test_args):
        """Test high frequency float topic with proper cleanup."""
        scenario = self.TEST_SCENARIOS[3]
        self.execute_test_scenario(scenario, test_args)

    # Helper methods
    def create_attr_enable_topic_client(self, node_name):
        """Create a client for the AttrEnableTopic service."""
        client = self.node.create_client(
            AttrEnableTopic, f"{node_name}/AttrEnableTopic"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /AttrEnableTopic not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def create_attr_disable_topic_client(self, node_name):
        """Create a client for the AttrDisableTopic service."""
        client = self.node.create_client(
            AttrDisableTopic, f"{node_name}/AttrDisableTopic"
        )
        self.assertTrue(
            client.wait_for_service(timeout_sec=SRV_TIMEOUT),
            f"Service /AttrDisableTopic not available after {SRV_TIMEOUT} seconds.",
        )
        return client

    def attr_enable_topic_request(self, client, attr_path, topic_name="", loop_rate=10.0, type=adi_iio.srv.AttrEnableTopic.Request.STRING):
        """Create and send a request to the AttrEnableTopic service."""
        request = AttrEnableTopic.Request()
        request.attr_path = attr_path
        request.topic_name = topic_name
        request.loop_rate = loop_rate
        request.type = type
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            f"Service call to /AttrEnableTopic did not complete within {SRV_TIMEOUT} seconds.",
        )
        return future

    def attr_disable_topic_request(self, client, topic_name, type):
        """Create and send a request to the AttrDisableTopic service."""
        request = AttrDisableTopic.Request()
        request.topic_name = topic_name
        request.type = type
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=SRV_TIMEOUT)
        self.assertTrue(
            future.done(),
            f"Service call to /AttrDisableTopic did not complete within {SRV_TIMEOUT} seconds.",
        )
        return future
