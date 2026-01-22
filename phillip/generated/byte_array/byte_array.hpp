
extern "C" struct ByteArray {
    unsigned char * data;
    int size;
};


extern "C" {
ByteArray byte_array_alloc(long long size);
void byte_array_free(ByteArray byte_array);
}