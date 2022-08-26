#include <CSerializer.h>
#include <stdlib.h>
#include <assert.h>

int32_t __CSerializer_get_net_step(const struct CSerializer_layout *layout, uint32_t i){
    if (layout->net_layout[2*i] < layout->net_layout[2*i+1]){
        return 1;
    }
    return -1;
}

uint32_t __CSerializer_get_net_start(const struct CSerializer_layout *layout, uint32_t i){
    if(layout->net_layout[2*i] < layout->net_layout[2*i+1]){
        return layout->net_layout[2*i];
    }
    return layout->net_layout[2*i] - 1;
}

/** @brief serializes given structure pointer into a given buffer.
 *  @param[in] host_obj pointer to a structure object being serialized.
 *  @param[out] network_buf pointer to a buffer for serialized object.
 *  @param[in] layout pointer to a serialization specification for this structure.
 */
void CSerializer_serialize(void *host_obj, uint8_t *network_buf, const struct CSerializer_layout *layout){
    uint8_t *host = (uint8_t *) host_obj;
    uint32_t i;
    for (i = 0; i < layout->num_members; ++i){
        uint32_t net_pos = __CSerializer_get_net_start(layout, i);
        int net_step = __CSerializer_get_net_step(layout, i);
        uint32_t host_pos = layout->host_layout[2*i];
        int host_step = 1;
        uint32_t len = layout->net_layout[2*i+1]-layout->net_layout[2*i];
        uint32_t b;
        for (b = 0; b < len; ++b){
            *(network_buf+net_pos) = *(host+host_pos);
            host_pos += host_step;
            net_pos += net_step;
        }
    }
}

/** @brief deserializes given buffer into given structure pointer.
 *  @param[in] network_buf pointer to a buffer being deserialized.
 *  @param[in] host_obj pointer to a structure target object.
 *  @param[in] layout pointer to a serialization specification for this structure.
 */
void CSerializer_deserialize(uint8_t *network_buf, void *host_obj, const struct CSerializer_layout *layout){
    uint8_t *host = (uint8_t *) host_obj;
    uint32_t i = 0;
    for (i = 0; i < layout->num_members; ++i){
        uint32_t net_pos = __CSerializer_get_net_start(layout, i);
        int net_step = __CSerializer_get_net_step(layout, i);
        uint32_t host_pos = layout->host_layout[2*i];
        int host_step = 1;
        uint32_t len = layout->net_layout[2*i+1]-layout->net_layout[2*i];
        uint32_t b;
        for (b = 0; b < len; ++b){
            *(host+host_pos) = *(network_buf+net_pos);
            host_pos += host_step;
            net_pos += net_step;
        }
    }
}

