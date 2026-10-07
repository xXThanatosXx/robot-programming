#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class SliderControl(Node):

    def __init__(self):
        super().__init__("slider_control")
        self.arm_pub_ = self.create_publisher(JointTrajectory, "arm_controller/joint_trajectory", 10)
        self.gripper_pub_ = self.create_publisher(JointTrajectory, "gripper_controller/joint_trajectory", 10)
        self.sub_ = self.create_subscription(JointState, "joint_commands", self.sliderCallback, 10)
        self.get_logger().info("Slider Control Node started")

    def sliderCallback(self, msg):
        arm_controller = JointTrajectory()
        gripper_controller = JointTrajectory()
        arm_controller.joint_names = ["joint_1", "joint_2", "joint_3"]
        gripper_controller.joint_names = ["joint_4"]

        arm_goal = JointTrajectoryPoint()
        gripper_goal = JointTrajectoryPoint()
        positions = dict(zip(msg.name, msg.position))
        if any(name not in positions for name in arm_controller.joint_names + gripper_controller.joint_names):
            self.get_logger().warning("Joint commands must include joint_1 through joint_4")
            return
        arm_goal.positions = [positions[name] for name in arm_controller.joint_names]
        gripper_goal.positions = [positions["joint_4"]]
        arm_goal.time_from_start.sec = 1
        gripper_goal.time_from_start.sec = 1

        arm_controller.points.append(arm_goal)
        gripper_controller.points.append(gripper_goal)

        self.arm_pub_.publish(arm_controller)
        self.gripper_pub_.publish(gripper_controller)


def main():
    rclpy.init()

    simple_publisher = SliderControl()
    rclpy.spin(simple_publisher)
    
    simple_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
