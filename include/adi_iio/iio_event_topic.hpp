// Copyright 2026 Analog Devices, Inc.
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

#ifndef ADI_IIO__IIO_EVENT_TOPIC_HPP_
#define ADI_IIO__IIO_EVENT_TOPIC_HPP_

#if defined(LIBIIO_V1)

#include <iio/iio.h>

#include <atomic>
#include <cerrno>
#include <iterator>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

#include <rclcpp/rclcpp.hpp>

#include "adi_iio/msg/iio_event.hpp"
#include "adi_iio/iio_node.hpp"

#define EVENT_QOS_QUEUE_SIZE 10

struct EventStreamDeleter final
{
  void operator()(iio_event_stream * stream) const noexcept {iio_event_stream_destroy(stream);}
};
using EventStreamPtr = std::unique_ptr<iio_event_stream, EventStreamDeleter>;

/// Owns an iio_event_stream*, destroying it (via EventStreamPtr) on scope exit
class EventStreamHandle final
{
public:
  EventStreamHandle() noexcept = default;

  /// Creates the stream for `dev` and moves it into `out` on success. Returns 0 on
  /// success or a negative errno decoded from iio_err() on failure.
  [[nodiscard]] static int create(const iio_device * dev, EventStreamHandle & out) noexcept
  {
    iio_event_stream * stream = iio_device_create_event_stream(dev);
    int err = iio_err(stream);
    if (err) {
      return err;
    }
    out.m_stream.reset(stream);
    return 0;
  }

  /// Reads one event into `out_event`. Returns 0 on success, `-EBUSY` if nonblock
  /// and the queue is empty, `-EINTR` if reset() ran concurrently (used to unblock
  /// a reader thread), `-EINVAL` if empty, or another negative errno.
  [[nodiscard]] int read(struct iio_event & out_event, bool nonblock) const noexcept
  {
    if (!m_stream) {
      return -EINVAL;
    }
    return iio_event_stream_read(m_stream.get(), &out_event, nonblock);
  }

  /// Destroys the owned stream, if any, unblocking a concurrent read().
  void reset() noexcept {m_stream.reset();}

  explicit operator bool() const noexcept {return static_cast<bool>(m_stream);}

private:
  EventStreamPtr m_stream;
};

/// Decode-only view over a raw iio_event.
struct EventView final : public iio_event
{
  explicit EventView(const struct iio_event & ev)
  : iio_event(ev) {}

  iio_event_type type() const noexcept {return iio_event_get_type(this);}
  iio_event_direction direction() const noexcept {return iio_event_get_direction(this);}

  /// NULL if there's no associated channel, or no differential partner when diff==true.
  const iio_channel * channel(const iio_device * dev, bool diff) const noexcept
  {
    return iio_event_get_channel(this, dev, diff);
  }

  /// Name for `type()`.
  const char * type_name() const noexcept
  {
    static constexpr const char * names[] = {
      "thresh",
      "mag",
      "roc",
      "thresh_adaptive",
      "mag_adaptive",
      "change",
      "mag_referenced",
      "gesture",
      "fault",
    };
    iio_event_type t = type();
    if (static_cast<unsigned>(t) < std::size(names)) {
      return names[t];
    }
    return "";
  }

  /// Name for `direction()`.
  const char * direction_name() const noexcept
  {
    static constexpr const char * names[] = {
      "either",
      "rising",
      "falling",
      "",  // IIO_EV_DIR_NONE: no direction
      "singletap",
      "doubletap",
      "fault_openwire",
    };
    iio_event_direction d = direction();
    if (static_cast<unsigned>(d) < std::size(names)) {
      return names[d];
    }
    return "";
  }
};

class IIOEventTopic final
{
public:
  IIOEventTopic(std::shared_ptr<IIONode> nh, std::string device_path);
  ~IIOEventTopic();

  [[nodiscard]] bool enableTopic(std::string & message, const std::string & topic_name = "");
  void disableTopic();

  const std::string & device_path() const {return m_device_path;}
  bool topic_enabled() const {return m_topic_enabled;}

private:
  void readLoop();
  adi_iio::msg::IIOEvent decode(const EventView & ev) const;

  std::shared_ptr<IIONode> m_nh;
  std::string m_device_path;
  std::string m_topic_name;
  iio_device * m_dev = nullptr;
  EventStreamHandle m_stream;

  bool m_topic_enabled = false;
  rclcpp::Publisher<adi_iio::msg::IIOEvent>::SharedPtr m_pub;
  std::thread m_th;
  std::atomic<bool> m_stopThread{false};
  std::mutex m_mutex;
};

#endif  // LIBIIO_V1

#endif  // ADI_IIO__IIO_EVENT_TOPIC_HPP_
