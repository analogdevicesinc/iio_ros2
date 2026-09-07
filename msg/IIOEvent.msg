# header.stamp = ROS receive time; header.frame_id = device path
std_msgs/Header header

# libiio event information
uint64 id
int64  hw_timestamp

# decoded event type
int8 TYPE_THRESH=0
int8 TYPE_MAG=1
int8 TYPE_ROC=2
int8 TYPE_THRESH_ADAPTIVE=3
int8 TYPE_MAG_ADAPTIVE=4
int8 TYPE_CHANGE=5
int8 TYPE_MAG_REFERENCED=6
int8 TYPE_GESTURE=7
int8 TYPE_FAULT=8
int8 type
# human-readable type name
string type_name

# decoded direction
int8 DIR_EITHER=0
int8 DIR_RISING=1
int8 DIR_FALLING=2
int8 DIR_NONE=3
int8 DIR_SINGLETAP=4
int8 DIR_DOUBLETAP=5
int8 DIR_FAULT_OPENWIRE=6
int8 direction
# human-readable direction name
string direction_name

string channel
string diff_channel
