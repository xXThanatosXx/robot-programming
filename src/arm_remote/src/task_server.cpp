#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <rclcpp_components/register_node_macro.hpp>
#include "arm_msgs/action/arm_task.hpp"
#include <moveit/move_group_interface/move_group_interface.hpp>

#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <map>
#include <chrono>
#include <controller_manager_msgs/srv/list_controllers.hpp>


using namespace std::placeholders;

namespace arm_remote
{
class TaskServer : public rclcpp::Node
{
public:
  explicit TaskServer(const rclcpp::NodeOptions& options = rclcpp::NodeOptions())
    : Node("task_server", options)
  {
    RCLCPP_INFO(get_logger(), "Starting the Server");
    action_server_ = rclcpp_action::create_server<arm_msgs::action::ArmTask>(
        this, "task_server", std::bind(&TaskServer::goalCallback, this, _1, _2),
        std::bind(&TaskServer::cancelCallback, this, _1),
        std::bind(&TaskServer::acceptedCallback, this, _1));
  }

  ~TaskServer() override { if (worker_.joinable()) worker_.join(); }

private:
  std::mutex groups_mutex_;
  std::weak_ptr<moveit::planning_interface::MoveGroupInterface> arm_group_, gripper_group_;
  std::thread worker_;
  std::atomic<bool> busy_{false};
  rclcpp_action::Server<arm_msgs::action::ArmTask>::SharedPtr action_server_;

  rclcpp_action::GoalResponse goalCallback(
      const rclcpp_action::GoalUUID& uuid,
      std::shared_ptr<const arm_msgs::action::ArmTask::Goal> goal)
  {
    RCLCPP_INFO(get_logger(), "Received goal request with id %d", goal->task_number);
    (void)uuid;
    if (goal->task_number < 0 || goal->task_number > 2 || busy_.exchange(true)) {
      return rclcpp_action::GoalResponse::REJECT;
    }
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse cancelCallback(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<arm_msgs::action::ArmTask>> goal_handle)
  {
    (void)goal_handle;
    RCLCPP_INFO(get_logger(), "Received request to cancel goal");
    std::lock_guard<std::mutex> lock(groups_mutex_);
    if (auto group = arm_group_.lock()) group->stop();
    if (auto group = gripper_group_.lock()) group->stop();
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void acceptedCallback(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<arm_msgs::action::ArmTask>> goal_handle)
  {
    // this needs to return quickly to avoid blocking the executor, so spin up a new thread
    if (worker_.joinable()) worker_.join();
    worker_ = std::thread{std::bind(&TaskServer::execute, this, _1), goal_handle};
  }

  void execute(const std::shared_ptr<rclcpp_action::ServerGoalHandle<arm_msgs::action::ArmTask>> goal_handle)
  {
    RCLCPP_INFO(get_logger(), "Executing goal");
    auto result = std::make_shared<arm_msgs::action::ArmTask::Result>();

    struct ResetBusy { std::atomic<bool> &flag; ~ResetBusy() { flag = false; } } reset{busy_};
    auto fail = [&]() { busy_ = false; result->success = false; if (goal_handle->is_canceling()) goal_handle->canceled(result); else goal_handle->abort(result); };
    try {
    // An action server can appear before ros2_control has activated its controllers.
    auto controllers = create_client<controller_manager_msgs::srv::ListControllers>(
        "/controller_manager/list_controllers");
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
    bool ready = false;
    while (rclcpp::ok() && std::chrono::steady_clock::now() < deadline) {
      if (goal_handle->is_canceling()) { fail(); return; }
      if (!controllers->wait_for_service(std::chrono::seconds(1))) continue;
      auto future = controllers->async_send_request(
          std::make_shared<controller_manager_msgs::srv::ListControllers::Request>());
      if (future.wait_for(std::chrono::seconds(1)) != std::future_status::ready) {
        controllers->remove_pending_request(future); continue;
      }
      int active = 0;
      const auto response = future.get();
      for (const auto &controller : response->controller) {
        if ((controller.name == "arm_controller" || controller.name == "gripper_controller" ||
             controller.name == "joint_state_broadcaster") && controller.state == "active") ++active;
      }
      if (active == 3) { ready = true; break; }
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    if (!ready) { RCLCPP_ERROR(get_logger(), "Controllers are not active"); fail(); return; }
    // MoveIt 2 Interface
    auto arm = std::make_shared<moveit::planning_interface::MoveGroupInterface>(shared_from_this(), "arm");
    auto gripper = std::make_shared<moveit::planning_interface::MoveGroupInterface>(shared_from_this(), "gripper");
    {
      std::lock_guard<std::mutex> lock(groups_mutex_);
      arm_group_ = arm; gripper_group_ = gripper;
    }
    auto &arm_move_group = *arm;
    auto &gripper_move_group = *gripper;
    arm_move_group.setStartStateToCurrentState();
    gripper_move_group.setStartStateToCurrentState();
    if (get_parameter("use_sim_time").as_bool()) {
      arm_move_group.setMaxVelocityScalingFactor(0.3);
      arm_move_group.setMaxAccelerationScalingFactor(0.3);
      gripper_move_group.setMaxVelocityScalingFactor(0.3);
      gripper_move_group.setMaxAccelerationScalingFactor(0.3);
    }

    std::vector<double> arm_joint_goal;
    std::vector<double> gripper_joint_goal;

    if (goal_handle->get_goal()->task_number == 0)
    {
      arm_joint_goal = {0.0, 0.0, 0.0};
      gripper_joint_goal = {-0.7};
    }
    else if (goal_handle->get_goal()->task_number == 1)
    {
      arm_joint_goal = {-1.14, -0.6, -0.07};
      gripper_joint_goal = {0.0};
    }
    else if (goal_handle->get_goal()->task_number == 2)
    {
      arm_joint_goal = {-1.57,0.0,-0.9};
      gripper_joint_goal = {0.0};
    }
    else
    {
      RCLCPP_ERROR(get_logger(), "Invalid Task Number");
      fail();
      return;
    }

    bool arm_within_bounds = arm_move_group.setJointValueTarget(arm_joint_goal);
    bool gripper_within_bounds = gripper_move_group.setJointValueTarget(std::map<std::string, double>{{"joint_4", gripper_joint_goal[0]}});
    if (!arm_within_bounds || !gripper_within_bounds)
    {
      RCLCPP_WARN(get_logger(),
                  "Target joint positions are outside the joint limits ");
      fail();
      return;
    }

    auto feedback = std::make_shared<arm_msgs::action::ArmTask::Feedback>();
    feedback->percentage = 10; goal_handle->publish_feedback(feedback);
    if (goal_handle->is_canceling()) { fail(); return; }
    moveit::planning_interface::MoveGroupInterface::Plan arm_plan;
    moveit::planning_interface::MoveGroupInterface::Plan gripper_plan;
    bool arm_plan_success = (arm_move_group.plan(arm_plan) == moveit::core::MoveItErrorCode::SUCCESS);
    bool gripper_plan_success = (gripper_move_group.plan(gripper_plan) == moveit::core::MoveItErrorCode::SUCCESS);
    
    if(arm_plan_success && gripper_plan_success)
    {
      RCLCPP_INFO(get_logger(), "Planning succeeded; executing arm and gripper trajectories");
      if (goal_handle->is_canceling()) {
        busy_ = false; result->success = false; goal_handle->canceled(result); return;
      }
      const auto arm_result = arm_move_group.execute(arm_plan);
      if (goal_handle->is_canceling()) {
        busy_ = false; result->success = false; goal_handle->canceled(result); return;
      }
      if (arm_result != moveit::core::MoveItErrorCode::SUCCESS) { fail(); return; }
      feedback->percentage = 60; goal_handle->publish_feedback(feedback);
      // Refresh the gripper start state after the arm trajectory finishes.
      gripper_move_group.setStartStateToCurrentState();
      if (gripper_move_group.plan(gripper_plan) != moveit::core::MoveItErrorCode::SUCCESS) {
        fail(); return;
      }
      if (goal_handle->is_canceling()) { fail(); return; }
      const auto gripper_result = gripper_move_group.execute(gripper_plan);
      if (goal_handle->is_canceling()) {
        busy_ = false; result->success = false; goal_handle->canceled(result); return;
      }
      if (arm_result != moveit::core::MoveItErrorCode::SUCCESS ||
          gripper_result != moveit::core::MoveItErrorCode::SUCCESS) { fail(); return; }
    }
    else
    {
      RCLCPP_ERROR(get_logger(), "One or more planners failed!");
      fail();
      return;
    }
  
    feedback->percentage = 100; goal_handle->publish_feedback(feedback);
    result->success = true;
    busy_ = false;
    goal_handle->succeed(result);
    RCLCPP_INFO(get_logger(), "Goal succeeded");
    } catch (const std::exception &error) {
      RCLCPP_ERROR(get_logger(), "Task failed: %s", error.what());
      if (goal_handle->is_canceling()) {
        busy_ = false; result->success = false; goal_handle->canceled(result);
      } else { fail(); }
    }
  }
};
}  // namespace arm_remote

RCLCPP_COMPONENTS_REGISTER_NODE(arm_remote::TaskServer)