#include "arm_controller/arm_interface.hpp"
#include <hardware_interface/types/hardware_interface_type_values.hpp>
#include <pluginlib/class_list_macros.hpp>
#include <cmath>


namespace arm_controller
{

std::string compensateZeros(const int value)
{
  std::string compensate_zeros = "";
  if(value < 10){
    compensate_zeros = "00";
  } else if(value < 100){
    compensate_zeros = "0";
  } else {
    compensate_zeros = "";
  }
  return compensate_zeros;
}
  
armInterface::armInterface()
{
}


armInterface::~armInterface()
{
  if (arduino_.IsOpen())
  {
    try
    {
      arduino_.Close();
    }
    catch (...)
    {
      RCLCPP_FATAL_STREAM(rclcpp::get_logger("armInterface"),
                          "Something went wrong while closing connection with port " << port_);
    }
  }
}


CallbackReturn armInterface::on_init(const hardware_interface::HardwareComponentInterfaceParams &params)
{
  CallbackReturn result = hardware_interface::SystemInterface::on_init(params);
  if (result != CallbackReturn::SUCCESS)
  {
    return result;
  }

  try
  {
    port_ = info_.hardware_parameters.at("port");
  }
  catch (const std::out_of_range &e)
  {
    RCLCPP_FATAL(rclcpp::get_logger("armInterface"), "No Serial Port provided! Aborting");
    return CallbackReturn::FAILURE;
  }

  if (info_.joints.size() != 4) {
    RCLCPP_ERROR(rclcpp::get_logger("armInterface"), "Expected four controlled joints");
    return CallbackReturn::ERROR;
  }

  position_commands_.assign(info_.joints.size(), 0.0);
  position_states_.assign(info_.joints.size(), 0.0);
  prev_position_commands_.assign(info_.joints.size(), 0.0);

  return CallbackReturn::SUCCESS;
}


std::vector<hardware_interface::StateInterface> armInterface::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  // Provide only a position Interafce
  for (size_t i = 0; i < info_.joints.size(); i++)
  {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
        info_.joints[i].name, hardware_interface::HW_IF_POSITION, &position_states_[i]));
  }

  return state_interfaces;
}


std::vector<hardware_interface::CommandInterface> armInterface::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  // Provide only a position Interafce
  for (size_t i = 0; i < info_.joints.size(); i++)
  {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
        info_.joints[i].name, hardware_interface::HW_IF_POSITION, &position_commands_[i]));
  }

  return command_interfaces;
}


CallbackReturn armInterface::on_activate(const rclcpp_lifecycle::State &previous_state)
{
  RCLCPP_INFO(rclcpp::get_logger("armInterface"), "Starting robot hardware ...");

  // Reset commands and states
  position_commands_ = { 0.0, 0.0, 0.0, 0.0 };
  prev_position_commands_ = { 0.0, 0.0, 0.0, 0.0 };
  position_states_ = { 0.0, 0.0, 0.0, 0.0 };

  try
  {
    arduino_.Open(port_);
    arduino_.SetBaudRate(LibSerial::BaudRate::BAUD_115200);
  }
  catch (...)
  {
    RCLCPP_FATAL_STREAM(rclcpp::get_logger("armInterface"),
                        "Something went wrong while interacting with port " << port_);
    return CallbackReturn::FAILURE;
  }

  RCLCPP_INFO(rclcpp::get_logger("armInterface"),
              "Hardware started, ready to take commands");
  return CallbackReturn::SUCCESS;
}


CallbackReturn armInterface::on_deactivate(const rclcpp_lifecycle::State &previous_state)
{
  RCLCPP_INFO(rclcpp::get_logger("armInterface"), "Stopping robot hardware ...");

  if (arduino_.IsOpen())
  {
    try
    {
      arduino_.Close();
    }
    catch (...)
    {
      RCLCPP_FATAL_STREAM(rclcpp::get_logger("armInterface"),
                          "Something went wrong while closing connection with port " << port_);
    }
  }

  RCLCPP_INFO(rclcpp::get_logger("armInterface"), "Hardware stopped");
  return CallbackReturn::SUCCESS;
}


hardware_interface::return_type armInterface::read(const rclcpp::Time &time,
                                                          const rclcpp::Duration &period)
{
  // Open Loop Control - assuming the robot is always where we command to be
  position_states_ = position_commands_;
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type armInterface::write(const rclcpp::Time &time,
                                                           const rclcpp::Duration &period)
{
  if (position_commands_ == prev_position_commands_)
  {
    // Nothing changed, do not send any command
    return hardware_interface::return_type::OK;
  }

  for (size_t i = 0; i < position_commands_.size(); ++i) {
    const double lower = -M_PI / 2;
    const double upper = i == 3 ? 0.0 : M_PI / 2;
    if (!std::isfinite(position_commands_[i]) || position_commands_[i] < lower - 1e-6 || position_commands_[i] > upper + 1e-6) {
      RCLCPP_ERROR(rclcpp::get_logger("armInterface"), "Invalid position command for joint %zu", i);
      return hardware_interface::return_type::ERROR;
    }
  }
  std::string msg;
  int base = static_cast<int>(((position_commands_.at(0) + (M_PI / 2)) * 180) / M_PI);
  msg.append("b");
  msg.append(compensateZeros(base));
  msg.append(std::to_string(base));
  msg.append(",");
  int shoulder = 180 - static_cast<int>(((position_commands_.at(1) + (M_PI / 2)) * 180) / M_PI);
  msg.append("s");
  msg.append(compensateZeros(shoulder));
  msg.append(std::to_string(shoulder));
  msg.append(",");
  int elbow = static_cast<int>(((position_commands_.at(2) + (M_PI / 2)) * 180) / M_PI);
  msg.append("e");
  msg.append(compensateZeros(elbow));
  msg.append(std::to_string(elbow));
  msg.append(",");
  int gripper = static_cast<int>(((-position_commands_.at(3)) * 180) / (M_PI / 2));
  msg.append("g");
  msg.append(compensateZeros(gripper));
  msg.append(std::to_string(gripper));
  msg.append(",");

  try
  {
    RCLCPP_INFO_STREAM(rclcpp::get_logger("armInterface"), "Sending new command " << msg);
    arduino_.Write(msg);
  }
  catch (...)
  {
    RCLCPP_ERROR_STREAM(rclcpp::get_logger("armInterface"),
                        "Something went wrong while sending the message "
                            << msg << " to the port " << port_);
    return hardware_interface::return_type::ERROR;
  }

  prev_position_commands_ = position_commands_;

  return hardware_interface::return_type::OK;
}
}  // namespace arm_controller

PLUGINLIB_EXPORT_CLASS(arm_controller::armInterface, hardware_interface::SystemInterface)
