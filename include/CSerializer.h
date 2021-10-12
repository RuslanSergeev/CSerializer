
#ifndef C_SERIALIZATION_H
#define C_SERIALIZATION_H

#include <stdint.h>

struct CSerializer_layout {
  const uint32_t num_members;       // number of members in a structure.
  const uint32_t net_len;           // buffer len
  const uint32_t host_len;          // struct sizeof
  const uint32_t *net_layout;       // {mem1_start, mem1_end, mem2_start, mem2_end, ...}
  const uint32_t *host_layout;      // {mem1_start, mem1_end, mem2_start, mem2_end, ...}
};

/** @brief check if generated layouts work fine on our machine.
 *  @param[in] type Type on which we want to check (without <struct> keyword) 
*/
#define CSerializer_check(type) (type ## _layout.host_len == sizeof(struct type))

void CSerializer_serialize(
  void *host_obj, 
  uint8_t *network_buf, 
  const struct CSerializer_layout *layout
);

void CSerializer_deserialize(
  uint8_t *network_buf, 
  void *host_obj, 
  const struct CSerializer_layout *layout
);

#endif //C_SERIALIZATION_H

