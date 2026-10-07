import time
import rclpy
from rclpy.action import ActionClient
from arm_msgs.action import ArmTask
rclpy.init();n=rclpy.create_node('verify_arm_task');c=ActionClient(n,ArmTask,'/task_server')
assert c.wait_for_server(timeout_sec=30)
invalid=ArmTask.Goal();invalid.task_number=99
f=c.send_goal_async(invalid);rclpy.spin_until_future_complete(n,f,timeout_sec=10)
assert not f.result().accepted
for number in (0,1,2):
 goal=ArmTask.Goal();goal.task_number=number
 f=c.send_goal_async(goal);rclpy.spin_until_future_complete(n,f,timeout_sec=15)
 h=f.result();assert h and h.accepted
 f=h.get_result_async();rclpy.spin_until_future_complete(n,f,timeout_sec=120)
 assert f.done(), 'Task timed out'
 print('Task',number,'status',f.result().status,'success',f.result().result.success,flush=True)
 assert f.result().result.success
n.destroy_node();rclpy.shutdown()
