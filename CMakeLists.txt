file(GLOB_RECURSE cserializer_src src/*.c)

add_library(cserializer_lib STATIC ${cserializer_src})
target_include_directories(cserializer_lib
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
