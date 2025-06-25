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
2. **Workspace Setup**: This package built in a ROS2 workspace using `colcon build`
3. **Hardware Requirements**:
   - An Analog Devices Pluto (PlutoSDR) device
   - USB connection to the host system
   - Device accessible via IP (typically `192.168.2.1` for USB-connected Pluto)

## Test Parameters

The test files accept several parameters that must be provided when running:

- `node_name`: Name for the test node instance (e.g., `"adi_node_test"`)
- `uri`: IIO device URI (e.g., `"ip:192.168.2.1"` for Pluto over USB)
- `timeout`: Service call timeout in seconds (e.g., `"5"`)

These parameters are passed through the launch system to configure the test
environment and target device.

## Running Tests

### Step-by-Step Test Execution

1. **Build the Package**
   ```bash
   cd /path/to/your/ros2_workspace
   colcon build --packages-select adi_iio
   source install/setup.bash
   ```

2. **Hardware Setup**
   - Connect your Pluto device via USB
   - Verify device connectivity:
     ```bash
     # Check if device is accessible
     iio_info -u ip:192.168.2.1
     ```

3. **Run All Tests with colcon**
   ```bash
   colcon test \
        --event-handlers console_direct+ \
        --base-paths ./src/iio_ros2 \
            node_name:="adi_node_test" \
            uri:="ip:192.168.2.1" \
            timeout:="5"
   ```

   **Command Explanation:**
   - `--event-handlers console_direct+`: Enables verbose console output for real-time test progress
   - `--base-paths ./src/iio_ros2`: Limits test execution to this specific package
   - The final arguments (e.g: `node_name`, `uri`, etc.) are test parameters passed to each test file

4. **View Test Results**
   ```bash
   colcon test-result --verbose
   ```

### Running Individual Tests

You can execute specific test files using `launch_test`:

```bash
# Example: Run attribute service tests
launch_test src/iio_ros2/test/attr_srv.test.py \
            node_name:="adi_node_test" \
            uri:="ip:192.168.2.1" \
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
            --ctest-args -R attr_srv \
            node_name:="adi_node_test" \
            uri:="ip:192.168.2.1" \
            timeout:="5"
```

Replace `attr_srv` with any substring matching the desired test file name (without the `.py` extension) to filter and run only those tests.

```bash
# Run only the smoke test
colcon test --event-handlers console_direct+ \
            --base-paths ./src/iio_ros2 \
            --ctest-args -R smoke \
            node_name:="adi_node_test" \
            uri:="ip:192.168.2.1" \
            timeout:="5"
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
