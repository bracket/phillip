
#include "byte_array.hpp"
#include <stdlib.h>




ByteArray byte_array_alloc_(long long size) {
    ByteArray out;
    
    out.data = (unsigned char*)malloc(size);
    out.size = size;
    
    return out;
}

void byte_array_free_(ByteArray byte_array) {
    free(byte_array.data);
}


extern "C" {
ByteArray byte_array_alloc(long long size) {
    return byte_array_alloc_(size);
}

void byte_array_free(ByteArray byte_array) {
    return byte_array_free_(byte_array);
}

}