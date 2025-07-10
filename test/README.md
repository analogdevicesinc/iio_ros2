# Overview

This directory contains system-level integration test definitions for the
`iio_ros2` package. These tests validate the functionality of the ADI IIO ROS2
node by launching the node and exercising its services and topics through
realistic usage scenarios.

## Integration with colcon

The tests are designed to integrate seamlessly with ROS2's `colcon` build and
test system. The package's `CMakeLists.txt` includes these launch tests within
the colcon test framework, enabling automated validation during continuous
integration and development workflows.

## Prerequisites

Before running these tests, ensure you have:

1. **ROS2 Environment**: A properly configured ROS2 installation (tested with ROS2 Humble)
2. **Workspace Setup**: This package will be built in a ROS2 workspace using `colcon build`
3. **Hardware Requirements**:
   - An Analog Devices Pluto (PlutoSDR) device
   - USB connection to the host system
   - Device accessible via IP (typically `192.168.2.1` for USB-connected Pluto)

## Test Parameters

The test files accept several parameters that must be provided when running:

- `node_name`: Name for the test node instance (e.g., `"adi_node_test"`)
- `uri`: IIO device URI (e.g., `"ip:192.168.2.1"` for Pluto over USB)
- `timeout`: Service call timeout in seconds (e.g., `"30"`)

These parameters are passed through the launch system to configure the test
environment and target device.
To change the default value for the test parameters you can use one of the
following environment variable: `TEST_NODE_NAME`, `TEST_URI`, `TEST_TIMEOUT`.

## Running Tests

### Step-by-Step Test Execution

1. **Enable tests that require HW**
   ```bash
   export IIO_ROS2_ENABLE_HW_TESTS=1
   ```
   This environment variable is used in CMake to enable the integration tests that require hardware. Without this variable set, the tests will be disabled during the build process
   and only linting tests will be performed.

2. **Configure test parameters (Optional)**
   ```bash
   export TEST_NODE_NAME="tester"
   export TEST_URI="ip:192.168.2.1"
   export TEST_TIMEOUT="60"
   ```
   These environment variables allow you to customize the test configuration before building. This step must be done before running `colcon build` since the variables are used by CMake during the build process. If not set, the following default values will be used:
   - `TEST_NODE_NAME`: defaults to `"adi_iio_node"`
   - `TEST_URI`: defaults to `"ip:192.168.2.1"`
   - `TEST_TIMEOUT`: defaults to `30` seconds

3. **Build the Package**
   ```bash
   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws/src
   git clone https://github.com/analogdevicesinc/iio_ros2.git
   cd ~/ros2_ws/

   colcon build \
      --symlink-install \
      --event-handlers console_cohesion+ \
      --packages-select adi_iio

   source install/setup.bash
   ```

4. **Hardware Setup**
   - Connect your Pluto device via USB
   - Verify device connectivity:
     ```bash
     # Check if device is accessible
     iio_info -u ip:192.168.2.1
     ```

5. **Run All Tests with colcon**
   ```bash
   colcon test \
        --event-handlers console_direct+
   ```

6. **View Test Results**
   ```bash
   colcon test-result --verbose
   ```

### Running Individual Tests

You can execute specific test files using `launch_test`:

```bash
# Example: Run attribute service tests
launch_test src/iio_ros2/test/attr_srv.test.py \
            node_name:="adi_node_test" \
            uri:="ip:192.168.2.2" \
            timeout:="5"

# Example: Run buffer service tests
launch_test src/iio_ros2/test/buffer_srv.test.py \
            node_name:="adi_node_test" \
            uri:="ip:192.168.2.1" \
            timeout:="5"
```

Alternatively, you can run specific tests by filtering with the `--ctest-args -R <pattern>` option in colcon. For example, to run only the `attr_srv.test.py` test file:

```bash
colcon test --event-handlers console_direct+ \
            --base-paths ./src/iio_ros2 \
            --ctest-args -R attr_srv
```

Replace `attr_srv` with any substring matching the desired test file name (without the `.py` extension) to filter and run only those tests.

```bash
# Run only the smoke test
colcon test --event-handlers console_direct+ \
            --base-paths ./src/iio_ros2 \
            --ctest-args -R smoke
```

### Debug Mode

For verbose debugging output, you can modify any test file to enable debug logging by uncommenting the debug arguments in the node configuration:

```python
# In any .test.py file, find the adi_iio_node definition and uncomment:
adi_iio_node = launch_ros.actions.Node(
    # ...existing configuration...
    arguments=[
        "--ros-args",
        "--log-level",
        "debug",
    ]
)
```

This will provide detailed logging from the IIO node during test execution.

## Test Files Description

- **`smoke_test.test.py`**: Basic node startup and service availability validation
- **`attr_srv.test.py`**: Attribute read/write service functionality tests
- **`attr_topic.test.py`**: Attribute topic enable/disable functionality tests
- **`buffer_srv.test.py`**: Buffer creation, data flow, and streaming tests
- **`iio_path_utils.test.py`**: IIO path discovery and validation tests

## Troubleshooting

- **Device Not Found**: Verify Pluto is connected and accessible at the specified URI
- **Permission Errors**: Ensure your user has access to USB devices (may require udev rules)
- **Test Timeouts**: Increase the timeout parameter if tests fail due to slow hardware response
- **Service Unavailable**: Check that the target device supports the required IIO capabilities

## References

- [ament_lint_auto](https://github.com/ament/ament_lint/blob/humble/ament_lint_auto/doc/index.rst)
- [How to configure ament python linters in CMakeLists?](https://answers.ros.org/question/351012/how-to-configure-ament-python-linters-in-cmakelists/)
- [Using black and flake8 in tandem](https://sbarnea.com/lint/black/)
