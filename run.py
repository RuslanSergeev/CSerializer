import json
from functools import reduce
import argparse
import os
from collections import OrderedDict

def _parse_config(config_name):
    json_file = open(config_name, 'r')
    desc = json.load(json_file, object_pairs_hook=OrderedDict)
    desc['host_layout'] = dict()
    desc['net_layout'] = dict()
    for t in desc['sizeof']:
        desc['host_layout'][t] = [[0, desc['sizeof'][t]['size']]]
    return desc

def _get_alignment(host_layout):
    ''' Gets the alignment of the structure datatype with a given
    `host_layout`. The alignment of a complex type is equal to the
    alignment of its biggest member.'''
    largest_member = max(host_layout, key=lambda mem: abs(mem[1]-mem[0]))
    return abs(largest_member[1]-largest_member[0])

def _get_sizeof(host_layout):
    alignment = _get_alignment(host_layout)
    no_padded_end = max(host_layout[-1])
    return _get_aligned_addr(no_padded_end, alignment)


def _get_aligned_addr(address, alignment):
    '''Gets first address, aligned to `alignment` equal or greater
    than the `address`.'''
    while address % alignment:
        address += 1
    return address

def _get_net_layout(struct, desc):
    ''' Returns layout of composed structure in buffer being sent.
    This layout is packed (no padding bytes between members).    
    Parameters:
        struct: (str)
            Name of the type for which the host layout is requested.
        desc: (str)
            json configuration string.
    Return:
        net_layout: (list(list(int)))
            [[member_start, member_end], ...]
            Same as host_layout, but with no padding bytes.
    '''
    net_layouts = desc['net_layout']
    if struct in net_layouts:
        return net_layouts[struct]
    host_layout = _get_host_layout(struct, desc)
    host_endiannes = desc['endiannes']['host']
    network_endiannes = desc['endiannes']['network']
    # get just sizeof of each component.
    net_layout = list(map(lambda m:  m[1]-m[0], host_layout))
    # make the components adresses grow.
    for i in range(1, len(net_layout)):
        net_layout[i] += net_layout[i-1]
    # make pairs [member_addr_begin, member_addr_end] 
    net_layout = list(map(list, zip([0]+net_layout, net_layout)))
    # revert long types in buffer if endiannes not match.
    endian_equals = lambda : host_endiannes == network_endiannes
    net_layout = [mem if endian_equals() else mem[-1::-1] for mem in net_layout]
    return net_layout

def _get_host_layout(struct, desc):
    ''' Generates structure in memory layout 
    (with padding bytes between structure members)
    Parameters:
        struct: (str)
            structure type name
        desc: (json object)
            a json description for all the structures and types.
    Return:
        host_layout: (list(list(int)))
            Layout of a structure in host memory.
            [[member_start, member_end], ...]
    '''
    host_layouts = desc['host_layout']
    if struct in host_layouts:
        return host_layouts[struct]
    else:
        #host_addr - size of the structure
        host_addr = 0
        #find nearest size aligned to `align`, given current size
        host_layout = []
        members = list(filter(lambda t: t!='comment', desc['structs'][struct]))
        for member in members:
            member_type = desc['structs'][struct][member]['type']
            # check if member is an array
            member_len  = desc['structs'][struct][member].get('len', 1)
            mem_layout = _get_host_layout(member_type, desc)
            mem_alignment = _get_alignment(mem_layout)
            host_addr = _get_aligned_addr(host_addr, mem_alignment)
            #increment member alignments by current offset and add it.
            do_offset = lambda mem: [mem[0]+host_addr, mem[1]+host_addr]
            # if the member is an array, add layouts for each element.
            for _ in range(member_len):
                host_layout += list(map(do_offset, mem_layout))
                host_addr += _get_sizeof(mem_layout)
        desc['host_layout'][struct] = host_layout
        return host_layout

def _align_comment(src_string, spaces_num=8):
    '''Given a source string with oneline c-style comment
    aligns the comment to a given number of spaces.
    Parameters:
        src_string: (str)
            c-source string with oneline comment.
    Return:
        src_string: (str)
            source string with the comment aligned'''
    align_src = lambda src, num: src if not len(src)%num else align_src(src+' ', num)
    if '//' in src_string:
        src, comment = src_string.split('//')
        src = align_src(src, spaces_num)
        return '//'.join([src, comment])
    else:
        return src_string

def _generate_c_structs(desc, path):
    '''Generates c-structs declarations header file.
    Parameters:
        desc: (json-object)
            A dictionary with structures description.
        path: (str)
            File path to save declarations in.'''
    hdir = os.path.dirname(path)
    if len(hdir):
        os.makedirs(hdir, exist_ok=True)
    with open(path, 'w') as out:
        guard = os.path.basename(path).split('.')[0]+'_H'
        print(f'#ifndef {guard}', file=out)
        print(f'#define {guard}', file=out)
        print('#include <stdint.h>', file=out)
        structs = desc['structs']
        make_comment = lambda comment: '// '+comment+'\n' if len(comment) else '\n'
        for struct in structs:
            comment = make_comment(structs[struct].get('comment', ''))
            print(f'{comment}struct {struct}','{', file=out)
            members = list(filter(lambda t: t!='comment', structs[struct]))
            for member in members:
                comment = make_comment(structs[struct][member].get('comment', ''))
                memtype = structs[struct][member]["type"]
                memtype = 'struct '+memtype if memtype in structs else memtype
                memlen = structs[struct][member].get("len", 1)
                # add brackets if the member is an array.
                member = member+f'[{memlen}]' if memlen > 1 else member
                src_string = f'    {memtype} {member}; {comment}'
                print(_align_comment(src_string, 16), end='', file=out)
            print('};', file=out)
        print(f'#endif //{guard}', file=out)

def _generate_c_layouts(desc, h_path, c_path):
    hdir = os.path.dirname(h_path)
    hbase = os.path.basename(h_path)
    cdir = os.path.dirname(c_path)
    if len(hdir):
        os.makedirs(hdir, exist_ok=True)
    if len(cdir):
        os.makedirs(cdir, exist_ok=True)
    guard = os.path.basename(h_path).split('.')[0]+'_H'
    with open(c_path, 'w') as c_out,\
        open(h_path, 'w') as h_out:
        print(f'#ifndef {guard}', file=h_out)
        print(f'#define {guard}\n', file=h_out)
        print(f'#include <CSerializer.h>', file=h_out)
        print(f'#include <{hbase}>', file=c_out)
        print(f'#include <stdint.h>', file=c_out)
        structs = desc['structs']
        for struct in structs:
            plain = lambda lst, mem: lst+mem
            host_layout = _get_host_layout(struct, desc)
            net_layout = _get_net_layout(struct, desc)
            host_plain = reduce(plain, host_layout)
            net_plain = reduce(plain, net_layout)
            print(f'extern struct CSerializer_layout {struct}_layout;', file=h_out)
            print(f'\nuint32_t {struct}_host_layout[] = ''{'+', '.join(map(str, host_plain))+'};', file=c_out)
            print(f'uint32_t {struct}_net_layout[] = ''{'+', '.join(map(str, net_plain))+'};', file=c_out)
            print(f'struct CSerializer_layout {struct}_layout =', '{', file=c_out)
            print(f'    .num_members={len(host_layout)},', file=c_out)
            print(f'    .net_len={max(net_layout[-1][0], net_layout[-1][1])},', file=c_out)
            print(f'    .host_len={_get_sizeof(host_layout)},', file=c_out)
            print(f'    .host_layout={struct}_host_layout,', file=c_out)
            print(f'    .net_layout={struct}_net_layout', '\n};', file=c_out)
        print(f'#endif // {guard}', file=h_out)

if __name__ == '__main__':

    description = '''\x1b[36m
    ############################################
            CSerializer generator script
    ############################################
        This script will generate header file definitions
        for structures described in the given config.
        As well it will generate definitions and declarations
        for serialization/deserialization for the given structures.
        Serialization/deserialization library files will also be generated.
    \x1b[0m'''
    epilog='''\x1b[36m
    --------------------------------------------
    CSerializer script (https://github.com/RuslanSergeev)
    \x1b[0m'''
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', default='config.json',
                        help='''Configuration file determines structures and types descriptions.''')
    parser.add_argument('--include', default='include',
                        help='''A path to generated header files.''')
    parser.add_argument('--src', default='src',
                        help='''A path to generated source files.''')
    parser.add_argument('--basename', default='structs',
                        help='''Basename for generated structs definitions and layouts files.
                        Example:
                               -basename cooltype: 
                               Next files will be generated:
                               {include}/cooltype.h - definitions for structs.
                               {include}/cooltype_layout.h - definitions for host and network layouts.
                               {include}/CSerializer.h - definition of common serializer structs and methods.
                               {src}/CSerializer.c - declaration of serializer methods.
                               {src}/cooltype_layout.c - declarations for host and network layouts.''')                           
    
    args=parser.parse_args()
    layout_header = f'{args.include}/{args.basename}_layout.h'
    layout_src = f'{args.src}/{args.basename}_layout.c'
    structs_header = f'{args.include}/{args.basename}.h'

    desc = _parse_config(args.config)
    _generate_c_layouts(desc, layout_header, layout_src)
    _generate_c_structs(desc, structs_header)
