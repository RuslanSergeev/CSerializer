# Documentation on CSerialization library

## What is CSerialization library about?
The CSerialization library is aim to provide a way  
to convert C structures (in host layout and with padding bytes in it)  
into a byte array that is in network layout without padding bytes in it.  

Following features supported:

 - Padding bytes filtering
    The padding bytes will be excluded from the serialized objects.
 - MSB or LSB bytes order
    User must explicitly specify host and network expected bytes order.
 - Structures inside structures.
    User specifies datatypes of structures members. Data type
    may be one of the structures defined previously or latelly by user.
    The ending padding bytes will be also filtered. The alignment
    of such structures inside other structures is also computed.
 - Arrays members
    Structures members may be arrays. 

Features to be added in future:

 - Bit-field members.
 

## How to use it?
Firstly you need to describe your C structures in JSON format (see how it works).  
Suppose you have a json file config json, and you call a library-generator  
script like this:  
```bash
python3 run.py  --config config.json --basename foo --src src --include include
```

The script will generate following files:
 - `foo.h` - our structure header.
 - `foo_layout.h` - a definition of the layout that only says `extern foo_layout;`.
 - `foo_layout.c` - a description how our structure is placed in host memory or in the network buffer, 
    so serialization code can transform `host`->`network` and vice versa.

*That's it! Now you can just use the generated files in your code!*

```C
#include <foo.h>            //generated from json
#include <foo_layout.h>     //generated from json
#include <CSerializer.h>    //generated

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
```

## How it works?

Specify your ANSI C structures in json format, e.g.: 
```json
{
    "structs": { 
        "foo": {
            "comment": "entire structure comment",
            "bar": { "type": "uint8_t", "comment": "single member comment"},
            "baz": { "type": "uint32_t" },
            "gaz": { "type": "uint32_t" }
        },
        "bar": {
            "b": { "type": "uint8_t", "len" : 2, "comment" : "array of 2 elements member" }, 
            "a": { "type": "foo" }
        }
    },
    "sizeof": {
        "uint8_t" : { "size"  : 1},
        "uint32_t": { "size"  : 4}
    },
    "endiannes": {
        "host": "little-endian",
        "network": "little-endian"
    }
}
```
Here user defines `foo` and `bar` structures, each containing some members.

Then we launch the generator script:
```sh
python3 run.py  --config config.json --basename foobar --src src --include include
```

The script will generate next filetree:
```
src/foobar_layout.c         - layout file for structures defined in the config: foo_layout, bar_layout
src/CSerializer.c           - serializer source file, contains the serialization functions.
include/CSerializer.h       - serializer header file with function definitions.
include/foobar.h            - definitions for foo and bar structures.
include/foobar_layout.c     - contains the values for foo_layout, bar_layout.
```
And that's it! You now can use generated files as it shown in the snippet above.
