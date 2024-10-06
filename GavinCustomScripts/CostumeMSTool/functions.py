def read_mgf_id_data(mgf_file, type):
    type_id = {"mzmine": "FEATURE_ID"}
    with open(mgf_file, 'r') as f:
        lines = f.readlines()

    return_data = {}
    flag = False
    entry_data = ""
    entry_id = ""
    for line in lines:
        if line.startswith("BEGIN IONS"):
            flag = True
            entry_data = ""
        if line.startswith("END IONS"):
            flag = False
            entry_data += line
            # entry = {entry_id: entry_data}
            return_data[entry_id] = entry_data
        if flag:
            if line.startswith(type_id[type]):
                entry_id = line.strip().split("=")[-1]
            entry_data += line
    return return_data


def read_txt_list(list_file):
    with open(list_file, "r") as f:
        lines = f.read().splitlines()
    return lines


def write_string(cont, file):
    with open(file, "w") as f:
        f.write(cont)
