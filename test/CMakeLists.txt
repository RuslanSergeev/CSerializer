cmake_minimum_required(3.7)

project(cserializer_tests)

add_custom_command(
    OUTPUT foo.h foo_layout.h foo_layout.c 
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/../run.py )

file(GLOB CSERIALIZER_TEST_SRC 
    ${CMAKE_CURRENT_SOURCE_DIR}/../src/*.c)

add_executable(cserializer_test 
    ${CSERIALIZER_TEST_SRC})

target_include_directories(cserializer_test 
    ${CMAKE_CURRENT_SOURCE_DIR}/../include 
    ${CMAKE_CURRENT_SOURCE_DIR}/include )