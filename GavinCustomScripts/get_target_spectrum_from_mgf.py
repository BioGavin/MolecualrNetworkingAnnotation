#! /usr/bin/env python3
import argparse
from typing import Dict

from CostumeMSTool import functions


def get_target_data(target_file, search_data: Dict):
    targets = functions.read_txt_list(target_file)
    target_data = ""
    for i in targets:
        target_i = search_data.get(i)
        if target_i:
            target_data += target_i
    return target_data


def help():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''get_target_spectrum_from_mgf.py -i search.mgf -t mzmine -l input_list -o target.mgf'''
    )

    parser.add_argument('-i', '--input_mgf', required=True, type=str)
    parser.add_argument('-l', '--input_list', required=True, type=str)
    parser.add_argument('-t', '--mgf_type', default="mzmine", type=str, choices=["mzmine"])
    parser.add_argument('-o', '--output_mgf', required=True, type=str)

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = help()
    data = functions.read_mgf_id_data(args.input_mgf, type=args.mgf_type)
    target_data = get_target_data(args.input_list, data)
    functions.write_string(target_data, args.output_mgf)
