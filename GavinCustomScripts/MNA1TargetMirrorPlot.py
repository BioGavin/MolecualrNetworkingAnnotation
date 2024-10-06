#! /usr/bin/env python3

import argparse
import os.path
import tempfile
import spectrum_utils.spectrum as sus
import matplotlib.pyplot as plt
import spectrum_utils.plot as sup
import json
from pyteomics import mgf
from pyteomics.auxiliary.structures import Charge


def read_mzmine_mgf(mzmine_mgf_dir):
    # 打开 mgf 文件进行解析
    indexed_mgf = mgf.read(mzmine_mgf_dir, index_by_feature_id=True)
    return indexed_mgf


def get_target_mzmine_mgf(indexed_mgf, target_id):
    target_mgf = indexed_mgf.get_spectrum(str(target_id))

    feature_id = target_mgf.get("params").get("feature_id")
    pepmass = target_mgf.get("params").get("pepmass")[0]
    charge = target_mgf.get("params").get("charge")[0]
    mz_array = target_mgf.get("m/z array")
    intensity_array = target_mgf.get("intensity array")

    spectrum = sus.MsmsSpectrum(identifier=feature_id, precursor_mz=pepmass, precursor_charge=charge,
                                mz=mz_array, intensity=intensity_array)
    return spectrum


def read_ccmslib_mgf(ccmslib_mgf_dir):
    indexed_mgf = mgf.read(ccmslib_mgf_dir, index_by_id=True)

    if indexed_mgf and len(indexed_mgf) == 1:
        id = indexed_mgf[0].get("params").get("id")
        pepmass = indexed_mgf[0].get("params").get("pepmass")[0]
        charge = indexed_mgf[0].get("params").get("charge")[0]
        mz_array = indexed_mgf[0].get("m/z array")
        intensity_array = indexed_mgf[0].get("intensity array")

        spectrum = sus.MsmsSpectrum(identifier=id, precursor_mz=pepmass, precursor_charge=charge,
                                    mz=mz_array, intensity=intensity_array)
        return spectrum
    else:
        raise Exception("Invalid MGF file input. Ensure that the MGF file contains only one spectrum data.")


def read_json_db(json_db_dir):
    with open(json_db_dir, 'r') as json_file:
        # 使用 json.load() 将 JSON 文件内容加载为 Python 字典
        db = json.load(json_file)
    return db


def get_target_db_mgf(db, target_id):
    target_spectrum = db[target_id]

    pepmass = float(target_spectrum.get("pepmass"))
    charge_value = target_spectrum.get("charge")
    ion_mode = target_spectrum.get("ion_mode")
    charge_symbol = '+' if ion_mode == 'positive' else '-'
    charge = Charge(charge_value + charge_symbol)
    ms2 = json.loads(target_spectrum["ms2"])
    mz_array = [item[0] for item in ms2]
    intensity_array = [item[1] for item in ms2]

    spectrum = sus.MsmsSpectrum(identifier=target_id, precursor_mz=pepmass, precursor_charge=charge,
                                mz=mz_array, intensity=intensity_array)
    return spectrum


def mirror_plot(spectrum_top, spectrum_bottom, output_pic, output_format="png"):
    fig, ax = plt.subplots(figsize=(12, 6))
    sup.mirror(spectrum_top, spectrum_bottom, spectrum_kws={"grid": False}, ax=ax)
    plt.savefig(output_pic, dpi=300, bbox_inches="tight", transparent=True, format=output_format)
    plt.close()
    # plt.show()


def help():
    parser = argparse.ArgumentParser(
        prog='mirrorplot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples: 
1. MNA1TargetMirrorPlot.py -i MZmine_Features_iimn_gnps.mgf -f 42 -c CCMSLIB00000000042 -o MirrorPlot
2. MNA1TargetMirrorPlot.py -i MZmine_Features_iimn_gnps.mgf -f 42 -I CCMSLIB00000000042.mgf -o MirrorPlot
        '''
    )

    parser.add_argument('-i', '--input1', required=True, type=str,
                        help="Input spectrum in mgf format from MZmine feature.")

    parser.add_argument('-f', '--feature_id', required=True, type=str,
                        help="FEATURE_ID of target spectrum in mgf format from MZmine feature.")

    parser.add_argument('-I', '--input2', required=False, type=str,
                        help="Input single spectrum in mgf format from GNPS database.")

    parser.add_argument('-c', '--ccmslib', required=False, type=str, help="ID of spectrum from GNPS database.")

    parser.add_argument('-d', '--db_dir', required=False, type=str, default=os.path.expanduser("~/.msdb/edb_info.json"),
                        help="Path to the MNA database in json format. Default: ~/.msdb/edb_info.json")

    parser.add_argument('-o', '--output_dir', required=True, type=str,
                        help="The folder where the output file is placed.")

    parser.add_argument('-m', '--output_format', required=False, type=str, default="png",
                        help="The format of the output file.")

    args = parser.parse_args()

    return args


def main():
    args = help()

    mzmine_mgf = read_mzmine_mgf(args.input1)
    top_spectrum = get_target_mzmine_mgf(mzmine_mgf, args.feature_id)

    if args.input2 and not args.ccmslib:

        bottom_spectrum = read_ccmslib_mgf(args.input2)
        ccmslib_id = os.path.basename(args.input2).split('.')[0]
    elif args.ccmslib and not args.input2:
        print(args.ccmslib)
        db = read_json_db(args.db_dir)
        bottom_spectrum = get_target_db_mgf(db, args.ccmslib)
        ccmslib_id = args.ccmslib
    else:
        raise Exception("Invalid input parameters."
                        "If specifying a single spectrum, use only the -I parameter."
                        "If searching from the database, use only the -c parameter.")

    output_file_name = f'{args.feature_id}_{ccmslib_id}.{args.output_format}'
    output_file_dir = os.path.join(args.output_dir, output_file_name)
    mirror_plot(top_spectrum, bottom_spectrum, output_file_dir, args.output_format)


if __name__ == '__main__':
    main()
