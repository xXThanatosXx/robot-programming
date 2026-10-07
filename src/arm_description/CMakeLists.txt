cmake_minimum_required(VERSION 3.5)
project(arm_description)


find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)

install(
  DIRECTORY launch meshes models urdf rviz config worlds
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(DIRECTORY scripts DESTINATION share/${PROJECT_NAME})

ament_package()