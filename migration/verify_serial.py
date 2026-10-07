import os, pty, subprocess, time, select, signal
import rclpy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
os.environ['ROS_DOMAIN_ID'] = '94'
master,slave=pty.openpty();port=os.ttyname(slave)
env=os.environ.copy();env['ROS_DOMAIN_ID']='94';env['ROS_LOG_DIR']='/tmp/arm_serial_validation'
log=open('/tmp/arm_serial_validation.log','w')
p=subprocess.Popen(['ros2','launch','arm_controller','controller.launch.py','is_sim:=false','port:='+port],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
 rclpy.init();node=rclpy.create_node('verify_serial_protocol');pub=node.create_publisher(JointTrajectory,'/arm_controller/joint_trajectory',10)
 deadline=time.monotonic()+35
 while time.monotonic()<deadline:
  rclpy.spin_once(node,timeout_sec=.1)
  if 'Configured and activated arm_controller' in open('/tmp/arm_serial_validation.log').read():break
 else:raise RuntimeError('Serial controller did not activate')
 msg=JointTrajectory();msg.joint_names=['joint_1','joint_2','joint_3'];point=JointTrajectoryPoint();point.positions=[.1,0.,0.];point.time_from_start.sec=1;msg.points=[point];pub.publish(msg)
 data=b'';deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  if select.select([master],[],[],.1)[0]:data+=os.read(master,4096)
 assert b'b095,s090,e090,g000,' in data, data
 print('Serial hardware plugin activated; Arduino protocol verified:',data[-60:])
 node.destroy_node();rclpy.shutdown()
finally:
 os.killpg(p.pid,signal.SIGINT)
 try:p.wait(timeout=10)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 os.close(master);os.close(slave);log.close()
