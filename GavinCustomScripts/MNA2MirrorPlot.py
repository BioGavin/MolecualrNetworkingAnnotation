#! /usr/bin/env python3

import argparse
import os.path
import tempfile
import spectrum_utils.spectrum as sus
from matplotlib import pyplot as plt
from pyteomics import mgf
import spectrum_utils.plot as sup


def read_MNA_result(MNA_result_folder):
    root_dir = os.path.abspath(MNA_result_folder)

    # 列出当前目录下的所有子目录
    sub_dirs = [os.path.join(root_dir, subdir) for subdir in os.listdir(root_dir) if
                os.path.isdir(os.path.join(root_dir, subdir))]

    ref_mgf = {}
    # 列出每个子目录下的mgf文件
    for subdir in sub_dirs:
        mgf_files = [os.path.join(subdir, mgf_dir) for mgf_dir in os.listdir(subdir) if mgf_dir.startswith("CCMSLIB")]
        if mgf_files:
            ref_mgf[os.path.basename(subdir)] = mgf_files
    return ref_mgf


def _preprocess_mgf(mgf_file, file_source):
    ref = {"mzmine": "FEATURE_ID",
           "ccmslib": "ID"}
    with open(mgf_file, "r") as f:
        content = f.read()

    content = content.replace(ref[file_source], "TITLE")

    if file_source == "ccmslib":
        content = content.replace("ENERGY", "")

    return content


def _read_target_mgf(mgf_file, target_id):
    spectra = mgf.read(mgf_file, use_index=True)
    for s in spectra:
        # print(s)
        title = s["params"]["title"]
        if title == target_id:
            pepmass = s["params"]["pepmass"][0]
            charge = int(s["params"]["charge"][0])
            mz_array = s["m/z array"]
            intensity_array = s["intensity array"]

            spectrum = sus.MsmsSpectrum(identifier=title, precursor_mz=pepmass, precursor_charge=charge,
                                        mz=mz_array, intensity=intensity_array)
            return spectrum


def get_top_spectrum(mgf_file, target_id):
    """top_spectrum是MZmine导出的Feature"""
    mgf_cont = _preprocess_mgf(mgf_file, "mzmine")
    mgf_temp = tempfile.NamedTemporaryFile(delete=True)
    mgf_temp.write(mgf_cont.encode("utf-8"))
    mgf_temp.seek(0)
    spectrum_top = _read_target_mgf(mgf_temp.name, target_id)
    mgf_temp.close()
    return spectrum_top


def _insert_charge_for_ccmslib(ccmslib_mgf_cont, charge="1+"):
    lines = ccmslib_mgf_cont.splitlines()
    lines.insert(3, f'CHARGE={charge}')
    content = '\n'.join(lines)
    return content


def _read_single_mgf(mgf_file):
    spectra = mgf.read(mgf_file, use_index=True)
    for s in spectra:
        title = s["params"]["title"]
        pepmass = s["params"]["pepmass"][0]
        charge = int(s["params"]["charge"][0])
        mz_array = s["m/z array"]
        intensity_array = s["intensity array"]

        spectrum = sus.MsmsSpectrum(identifier=title, precursor_mz=pepmass, precursor_charge=charge,
                                    mz=mz_array, intensity=intensity_array)
        # spectrum.annotate_proforma()
        return spectrum


def get_bottom_spectrum(ccmslib_mgf):
    """bottom_spectrum是MNA匹配的CCMSLIB"""
    mgf_cont = _preprocess_mgf(ccmslib_mgf, "ccmslib")
    mgf_cont = _insert_charge_for_ccmslib(mgf_cont)
    mgf_temp = tempfile.NamedTemporaryFile(delete=True)
    mgf_temp.write(mgf_cont.encode("utf-8"))
    mgf_temp.seek(0)
    spectrum_bottom = _read_single_mgf(mgf_temp.name)
    mgf_temp.close()
    return spectrum_bottom


def mirror_plot(spectrum_top, spectrum_bottom, output_pic, output_format="png"):
    fig, ax = plt.subplots(figsize=(12, 6))
    sup.mirror(spectrum_top, spectrum_bottom, spectrum_kws={"grid": False}, ax=ax)
    plt.savefig(output_pic, dpi=300, bbox_inches="tight", transparent=False, format=output_format)
    plt.close()


def help():
    parser = argparse.ArgumentParser(
        prog='mna2mirrorplot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''mna2mirrorplot -i MNA_result_folder -m MNA_input_mgf -o mirror_plot_folder'''
    )

    parser.add_argument('-i', '--input_folder', required=True, type=str)
    parser.add_argument('-m', '--input_mgf', required=True, type=str)
    parser.add_argument('-o', '--output_folder', required=True, type=str)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = help()
    # 1. 解析MNA输出文件夹，获取所有子文件夹中CCMSLIB的mgf文件
    """构建一个字典ref_mgf = {"id": [CCMSLIB1.mgf, CCMSLIB2.mgf],...}"""
    ref_mgf = read_MNA_result(args.input_folder)

    # 2. 遍历绘图
    for feature_id, ccmslib_mgf_ls in ref_mgf.items():
        spectrum_top = get_top_spectrum(args.input_mgf, feature_id)
        for ccmslib_mgf in ccmslib_mgf_ls:
            spectrum_bottom = get_bottom_spectrum(ccmslib_mgf)
            output_png_name = "_".join([feature_id, os.path.splitext(os.path.basename(ccmslib_mgf))[0]]) + ".png"
            print(f"Mirror Plot: {output_png_name}")
            output_png_dir = os.path.join(args.output_folder, output_png_name)
            mirror_plot(spectrum_top, spectrum_bottom, output_png_dir)
