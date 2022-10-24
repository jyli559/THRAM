cmake_minimum_required(VERSION 3.1)
set(PROJECT_NAME llvm-cdfg)
project(${PROJECT_NAME} VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 14)
# set(CMAKE_BUILD_TYPE "Release")

set(LLVM_INCLUDE_DIRS "/media/yhqiu/HDD/home/yhqiu/llvm/llvm-10.0.0-built/usr/local/include")
set(LLVM_LIBRARY_DIRS "/media/yhqiu/HDD/home/yhqiu/llvm/llvm-10.0.0-built/usr/local/lib")
# find_package(LLVM REQUIRED CONFIG)
# add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})
link_directories(${LLVM_LIBRARY_DIRS})

add_subdirectory(llvm-pass)  
