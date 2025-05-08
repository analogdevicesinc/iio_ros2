// Copyright 2025 Analog Devices, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef ADI_IIO__IIO_PATH_HPP_
#define ADI_IIO__IIO_PATH_HPP_

#include <vector>
#include <string>
#include <sstream>
#include <utility>

enum IIOPathType
{
  CONTEXT,
  CONTEXT_ATTR,
  DEVICE,
  DEVICE_ATTR,
  CHANNEL,
  CHANNEL_ATTR,
};

/**
 * @class IIOPath
 * @brief Represents and manipulates Industrial I/O (IIO) paths that are used to
 * uniquely identify IIO devices, attributes, and channels from a context.
 *
 * Examples of valid paths types:
 * - CONTEXT: ""
 * - CONTEXT_ATTR: "context-attribute"
 * - DEVICE: "device-name"
 * - DEVICE_ATTR: "device-name/attribute-name"
 * - CHANNEL: "device-name/chn-prefix_channel-name"
 * - CHANNEL_ATTR: "device-name/chn-prefix_channel-name/attribute-name"
 */
class IIOPath
{
public:
  /**
   * @brief Constructs an IIOPath object.
   *
   * @param path The base path for the IIO object.
   * @param delimiter The character used to separate path segments (default is '/').
   */
  explicit IIOPath(std::string path, char delimiter = '/');

  /**
   * @brief Retrieves the original path used to create this object.
   *
   * @return The base path as a string.
   */
  std::string basePath() const;

  /**
   * @brief Extracts the context attribute segment from the path.
   *
   * @return The context attribute as a string.
   */
  std::string getContextAttrSegment() const;

  /**
   * @brief Extracts the device name segment from the path.
   *
   * @return The device name as a string.
   */
  std::string getDeviceSegment() const;

  /**
   * @brief Extracts the device attribute segment from the path.
   *
   * @return The device attribute as a string.
   */
  std::string getDeviceAttrSegment() const;

  /**
   * @brief Extracts the channel name segment from the path.
   *
   * @return The channel name as a string.
   */
  std::string getChannelSegment() const;

  /**
   * @brief Extracts the channel information segment from the path.
   *
   * @return A pair containing a boolean indicating if the channel is of output
   * type and the channel name as a string.
   * @note The boolean variable helps to uniquely identify channels with
   * the same name but different types (input/output).
   */
  std::pair<bool, std::string> getExtendedChannelSegment() const;
  static std::pair<bool, std::string> getExtendedChannelSegment(std::string chn_segment);


  /**
   * @brief Whether the channel segment has the extended syntax format.
   *
   */
  bool hasExtendedChannelFormat() const;
  static bool hasExtendedChannelFormat(std::string chn_segment);

  /**
   * @brief Extracts the channel attribute segment from the path.
   *
   * @return The channel attribute as a string.
   */
  std::string getChannelAttrSegment() const;

  /**
   * @brief Appends a suffix to the current IIO path.
   *
   * The suffix is used to create a new path pointing to a specific attribute
   * or nested element.
   *
   * @param suffix The string to append to the base path.
   * @return The updated path as a string.
   */
  std::string append(const std::string & suffix);

  /**
   * @brief Validates the current IIO path based on the specified type.
   *
   * This function checks if the current path conforms to the expected structure
   * for the given IIOPathType. It ensures that the path contains the necessary
   * segments and follows the correct format for the specified type.
   *
   * @param type The type of IIO path to validate (e.g., `CONTEXT`, `DEVICE`, `CHANNEL`).
   * @return True if the path is valid for the specified type, false otherwise.
   */
  bool isValid(const IIOPathType type);

  /**
   * @brief Splits a string into segments based on the delimiter.
   *
   * @param str The input string to be split.
   * @return A vector of substrings obtained by splitting the input string.
   */
  std::vector<std::string> split(const std::string & str);

  /**
   *
   * @brief Constructs the channel segment of the path.
   *
   * @param output A boolean indicating if the channel is an output channel.
   * @param chn_name The name of the channel.
   * @return The constructed channel segment as a string.
   */
  static std::string toExtendedChannelSegment(bool output, std::string chn_name);

  /**
   * @brief Converts a path to a ROS2 topic name.
   *
   * @param path The input path to be converted.
   * @return The converted topic name as a string.
   *
   * @note ROS2 topic names cannot contain '-' characters.
   */
  static std::string toTopicName(std::string path);

private:
  std::string m_base_path;
  char m_delimiter;
  std::vector<std::string> m_segments;
};

#endif  // ADI_IIO__IIO_PATH_HPP_
