#! /usr/bin/env python3

import argparse
import tempfile

import matplotlib.pyplot as plt
import spectrum_utils.plot as sup
import spectrum_utils.spectrum as sus
from pyteomics import mgf


def preprocess_mgf(mgf_file, file_source):
    ref = {"mzmine": "FEATURE_ID",
           "ccmslib": "ID"}
    with open(mgf_file, "r") as f:
        content = f.read()

    content = content.replace(ref[file_source], "TITLE")

    if file_source == "ccmslib":
        content = content.replace("ENERGY", "")

    return content


def read_mgf(mgf_file):
    spectra = mgf.read(mgf_file, use_index=True)
    for s in spectra:
        # print(s)
        title = s["params"]["title"]
        pepmass = s["params"]["pepmass"][0]
        charge = int(s["params"].get("charge", [1])[0])
        mz_array = s["m/z array"]
        intensity_array = s["intensity array"]

        spectrum = sus.MsmsSpectrum(identifier=title, precursor_mz=pepmass, precursor_charge=charge,
                                    mz=mz_array, intensity=intensity_array)
        # spectrum.annotate_proforma()
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
        epilog='''mirrorplot -i input1.mgf -t mzmine -I input2.mgf -T ccmslib -o mirror.png'''
    )

    parser.add_argument('-i', '--input_spec1', required=True, type=str)
    parser.add_argument('-I', '--input_spec2', required=True, type=str)

    parser.add_argument('-t', '--input1_type', required=True, type=str)
    parser.add_argument('-T', '--input2_type', required=True, type=str)

    parser.add_argument('-o', '--output_png', required=True, type=str)
    parser.add_argument('-f', '--output_format', default="png", type=str, choices=["png", "svg"])

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = help()

    mgf1_cont = preprocess_mgf(args.input_spec1, args.input1_type)
    mgf2_cont = preprocess_mgf(args.input_spec2, args.input2_type)

    mgf1_temp = tempfile.NamedTemporaryFile(delete=True)
    mgf1_temp.write(mgf1_cont.encode("utf-8"))
    mgf1_temp.seek(0)

    mgf2_temp = tempfile.NamedTemporaryFile(delete=True)
    mgf2_temp.write(mgf2_cont.encode("utf-8"))
    mgf2_temp.seek(0)

    spectrum_top = read_mgf(mgf1_temp)
    spectrum_bottom = read_mgf(mgf2_temp)

    mgf1_temp.close()
    mgf2_temp.close()

    mirror_plot(spectrum_top, spectrum_bottom, args.output_png, args.output_format)
