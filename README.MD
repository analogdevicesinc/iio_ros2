# ADI IIO Node

## Overview

The `adi_iio_node` is a ROS 2 node that interfaces with Analog Devices IIO devices.
It provides a collection of services to read/write IIO attributes, and manage IIO buffers. You can also attach topics to the attributes/buffers

## Parameters

The node accepts the following parameters:

- `uri`: The URI of the IIO device (e.g., `ip:192.168.2.1`).

## Services

TODO: add get attributes/ get devices/ get channels services
TODO: add examples for each service

The node provides the following services:

<details>
<summary>AttrReadString</summary>

Reads an IIO attribute as a string

**Request:**
- `attr_path` (string): The path to the attribute to be read.

**Response:**
- `value` (string): The value of the attribute.
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>AttrWriteString</summary>

Writes an IIO attribute as a string

**Request:**
- `attr_path` (string): The path to the attribute to be written.
- `value` (string): The value to be written to the attribute.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>
AttrEnableTopic: Enables a topic for a specific attribute.</summary>
Enables a topic for a specific attribute.

**Request:**
- `attr_path` (string): The path to the attribute to be enabled.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>AttrDisableTopic</summary>

Disables a topic for a specific attribute.

**Request:**
- `attr_path` (string): The path to the attribute to be disabled.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>BufferRead</summary>

Reads data from a buffer.

**Request:**
- `device_path` (string): The path to the device.
- `samples_count` (int): The number of samples to read.

**Response:**
- `buffer` (Int32Multiarray): The data read from the buffer.
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>

<summary>BufferWrite</summary>

Writes data to a buffer.

**Request:**
- `device_path` (string): The path to the device.
- `buffer` (Int32Multiarray): The data to be written to the buffer.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>BufferRefill</summary>

Refills a buffer.

**Request:**
- `device_path` (string): The path to the device.

**Response:**
- `buffer` (Int32Multiarray): The data read from the buffer after refilling.
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>BufferCreate</summary>

Creates a buffer.

**Request:**
- `device_path` (string): The path to the device.
- `samples_count` (int): The number of samples for the buffer.
- `channels` (array of string): The channels to be included in the buffer.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>BufferDestroy</summary>

Destroys a buffer.

**Request:**
- `device_path` (string): The path to the device.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>BufferEnableTopic</summary>

Enables a topic for a buffer.

**Request:**
- `device_path` (string): The path to the device.
- `topic` (string): The topic to be enabled.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

<details>
<summary>BufferDisableTopic</summary>

Disables a topic for a buffer.

**Request:**
- `device_path` (string): The path to the device.
- `topic` (string): The topic to be disabled.

**Response:**
- `success` (boolean): Indicates if the operation was successful.
- `message` (string): A message providing additional information.

</details>

## Node-Specific Concepts

#### Channel and Device Attribute path
The `attr_path` parameter is used to specify the path to a specific attribute within an IIO device. This path follows the structure of the IIO context hierarchy.

Example:
- An attribute path to a channel attribute might look like `ad5592r/voltage0/raw`, where `ad5592r` is the device name, `voltage0` is the channel, and `raw` is the attribute.
- A path to a device attribute would be `ad9361-phy/calib_mode`

#### Topic name resolution

The `EnableTopic` services can take an optional topic_name parameter. When enabling the topic, the topic_name will be used. The default value for this parameter is "". When this value is used, the specific device/channel attribute name will be used prefixed with the node name. For topics that deal with attributes, two topics will be created for read/write operations to the attribute. These topics will be suffixed with `/read` and `/write`. To adhere to ROS2 topic naming standards, "-" will be replaced by "_".

Example:
- An adi-iio node named "radio" that enables the topic "/cf-ad9361-lpc/voltage0/sampling_frequency" will publish "/radio/cf_ad9361_lpc/voltage0/sampling_frequency/read" and be subscribed to "/radio/cf_ad9361_lpc/voltage0/sampling_frequency/write" for updates.

#### Service responses

All services responses contain at least two fields: a boolean indicating success and a string message.

```
AttrReadString.srv:

string attr_path
---
bool success
string message
```

If the service operation is successful, the success boolean is set to `true`, and the message will be "Success". In case of failure, success boolean is set to false. The returned message contains the errno returned by the iio command along with the string interpretation of that errno.


#### Buffers

A buffer is a continuous data capture from a device. There are a few operations that you can do with IIO buffers.

Create buffer - the device start capturing data
Refill buffer - the data is transported from the device to the client via Int32MultiArray buffer in a service response
Enable buffer topic - the node starts a continuous capture and publishes acquired data on the associated topic
Destroy buffer - the device stops capturing data
Read buffer - a convenience operation that bundles create and refill into one service

When creating a buffer a channels array is required as a parameter for the service request. An example of such an array would be:

- ```{"voltage0"}``` - for a single channel or
- ```{"voltage0","voltage1","voltage2","voltage3"}``` - multiple channels

The data is bundled in an Int32MultiArray. Data is interlleaved in the buffer and the buffer dimensions represent number of samples and number of channels.
A request that acquires data from ```{"voltage0","voltage1"}``` the buffer would look like this

{voltage0_sample0, voltage1_sample0, voltage0_sample1, voltage1_sample1, voltage0_sample2, voltage1_sample2 .... }

## Launch files

To launch the node, you can use the provided launch file `dev_adi_iio_launch.py`. This launch file sets the necessary ```uri``` parameter. URI
There is a small python script to visualize the waveform using matplotlib plots. The ```topic``` parameter is used to subscribe to the topic where the waveform is published and plot the waveforms.

```sh
ros2 launch adi_iio_node dev_adi_iio_launch.py
python3 visualize_iio_waveform.py --topic /m2k_adc
```



## Dependencies

Ensure that the following dependencies are installed:

- `rclcpp`
- `std_msgs`
- `rosidl_default_generators`
- `rosidl_typesupport_introspection_cpp`
- `libiio` - libiio-v0 branch

## Building

To build the package, you must first install the libiio dependency

Install from source

```sh
git clone https://github.com/analogdevicesinc/libiio
cd libiio
git checkout libiio-v0
mkdir build && cd build
cmake ../
make
sudo make install
```

Install from deb package
```sudo apt-get install libiio-dev```


Navigate to your workspace and run:
```sh
colcon build
source install/setup.bash
```
