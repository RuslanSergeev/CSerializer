#include <foo.h>            //generated from json
#include <foo_layout.h>     //generated from json
#include <CSerializer.h>    //generated


int main(int argc, char *argv[]){

    // Lets look at serialization first:
    struct foo foo_obj;
    foo.bar = 0xAA;
    foo.baz = 0xDEAD;
    foo.gaz = 0xBEAF;
    // Check if generated code works on our architecture:
    assert(CSerializer_check(foo)); // expecting true.
    uint8_t buffer[foo_layout.net_len];
    // use serialization method and foo_layout, that were generated:
    CSerializer_serialize(&foo_obj, buffer, &foo_layout);
    // Now we can send this serialized object with no padding bytes in it:
    Serial.write(buffer, foo_layout.net_len);

    //Now let's deserialize buffer into object:
    struct foo foo_deserialized;
    CSerializer_deserialize(buffer, &foo_deserialized, &foo_layout);

    // Check serialization<->deserialization works good.
    assert(foo_deserialized.bar == foo_obj.bar);
    assert(foo_deserialized.baz == foo_obj.baz);
    assert(foo_deserialized.gaz == foo_obj.gaz);

    return 0;
}
