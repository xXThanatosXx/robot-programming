#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <trajectory_msgs/msg/joint_trajectory_point.hpp>

#include <chrono>
#include <algorithm>


using namespace std::chrono_literals;
using std::placeholders::_1;

class SliderControl : public rclcpp::Node
{
public:
  SliderControl() : Node("slider_control")
  {
    sub_ = create_subscription<sensor_msgs::msg::JointState>(
        "joint_commands", 10, std::bind(&SliderControl::sliderCallback, this, _1));
    arm_pub_ = create_publisher<trajectory_msgs::msg::JointTrajectory>("arm_controller/joint_trajectory", 10);
    gripper_pub_ = create_publisher<trajectory_msgs::msg::JointTrajectory>("gripper_controller/joint_trajectory", 10);
    RCLCPP_INFO(get_logger(), "Slider Control Node started");
  }

private:
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr sub_;
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr arm_pub_;
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr gripper_pub_;

  void sliderCallback(const sensor_msgs::msg::JointState &msg) const
  {
    trajectory_msgs::msg::JointTrajectory arm_command, gripper_command;
    arm_command.joint_names = {"joint_1", "joint_2", "joint_3"};
    gripper_command.joint_names = {"joint_4"};

    trajectory_msgs::msg::JointTrajectoryPoint arm_goal, gripper_goal;
    for (const auto &name : {"joint_1", "joint_2", "joint_3", "joint_4"}) {
      const auto it = std::find(msg.name.begin(), msg.name.end(), name);
      const auto index = static_cast<std::size_t>(std::distance(msg.name.begin(), it));
      if (it == msg.name.end() || index >= msg.position.size()) {
        RCLCPP_WARN(get_logger(), "Joint commands must include joint_1 through joint_4");
        return;
      }
      if (index < msg.position.size()) {
        if (std::string(name) == "joint_4") {
          gripper_goal.positions.push_back(msg.position[index]);
        } else {
          arm_goal.positions.push_back(msg.position[index]);
        }
      }
    }
    arm_goal.time_from_start.sec = 1;
    gripper_goal.time_from_start.sec = 1;
    
    arm_command.points.push_back(arm_goal);
    gripper_command.points.push_back(gripper_goal);
    
    arm_pub_->publish(arm_command);
    gripper_pub_->publish(gripper_command);
  }
};


int main(int argc, char* argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SliderControl>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
