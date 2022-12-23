import json
import difflib
import re


def integrate_picture_boxes(boxes, texts):    # 1todo  2022-3-10 9:00
    temp_list = []
    result = []
    tag = (boxes[4][2][1] - boxes[4][1][1]) * 2 // 3
    for box in boxes:
        temp_list.append(box[0][1])
    i, j = 0, 1
    end_len = len(temp_list)
    while j < end_len:
        temp = [i]
        while True:
            if j < end_len and abs(temp_list[i] - temp_list[j]) < tag:
                temp.append(j)
                j += 1
            else:
                break
        result.append(temp)
        i = j
        j += 1

    result_text_boxes = []
    for a_list in result:
        if len(a_list) < 2:
            result_text_boxes.append(texts[a_list[0]])
        elif len(a_list) == 2:
            result_text_boxes.append(texts[a_list[0]] + "+" + texts[a_list[1]])
        else:
            string = texts[a_list[0]] + "+" + texts[a_list[1]]
            for i in a_list[2:]:
                string = string + " " + texts[i]
            result_text_boxes.append(string)
    return extract_content(result_text_boxes)


def merge_next_inf(result_dict, texts):

    # step1 :定位， 哪个位置多了   Nama , Alamat
    # Nama
    try:
        a = re.sub('[^A-Za-z0-9 ]+', '', texts[4])
        if a.isalpha():
            texts[3] = texts[3] + " " + a
            texts.remove(a)

        sim = difflib.SequenceMatcher(None, texts[7], "RT/RW+00*/00*").quick_ratio()  # 0.28
        if sim < 0.21:
            texts[6] = texts[6] + " " + texts[7]
            texts.remove(texts[7])
        for i_dict, text in zip(result_dict, texts):
            result_dict[i_dict] = text
    except Exception as e:
        print(e)
        for i_dict, text in zip(result_dict, texts):
            result_dict[i_dict] = text


def judge_starts_with(string):
    if string.startswith(" ", 0, 1):
        return string[1:]
    return string


def select_PROVINSI(text_dict):
    provinsi = text_dict["PROVINSI"]
    try:
        text_dict["PROVINSI"] = judge_starts_with(provinsi[8:])
    except:
        text_dict["PROVINSI"] = provinsi
def select_NIK(text_dict):
    nik = text_dict["NIK"]
    text_dict["NIK"] = re.sub('[^0-9]+', '', nik)
def select_Nama(text_dict):
    nama = text_dict["Nama"]
    if len(nama.split("+")) > 1:
        temp1 = re.sub('[^A-Za-z ]+', '', nama.split("+")[0])
        temp2 = re.sub('[^A-Za-z ]+', '', nama.split("+")[1])
        if temp2.isupper():
            text_dict["Nama"] = judge_starts_with(temp2)
        else:
            text_dict["Nama"] = judge_starts_with(temp1)
    else:
        temp = re.sub('[^A-Za-z ]+', '', nama)
        text_dict["Nama"] = judge_starts_with(temp)
def maybe_without(strings):
    count = 3   # 1todo 2022-3-14 10:50 根据实际，动态调整大写字母个数
    location = 0
    for index, al in enumerate(strings):
        if not strings[index].isupper():
            location = index
        if index - location == count:
            return strings[location+1:]
    return strings
def select_Tempat(text_dict):
    Tempat_TglLahir = text_dict["Tempat/TglLahir"]
    if len(Tempat_TglLahir.split("+")) > 1:
        a = re.sub('[^A-Z]+', '', Tempat_TglLahir.split("+")[0])
        b = re.sub('[^A-Z]+', '', Tempat_TglLahir.split("+")[1])
        if len(a) > len(b):
            temp = re.sub('[^A-Za-z0-9]+', '', Tempat_TglLahir.split("+")[0])
        else:
            temp = re.sub('[^A-Za-z0-9]+', '', Tempat_TglLahir.split("+")[1])
    else:
        a = maybe_without(Tempat_TglLahir)
        temp = re.sub('[^A-Z0-9 ]+', '', a)
    index = len(re.sub('[^A-Z ]+', '', temp))
    Tempat = temp[0:index]
    Tglahir = temp[index:]
    try:
        Tglahir = Tglahir[0:2] + "-" + Tglahir[2:4] + "-" + Tglahir[-4:]
    except Exception as e:
        print("Tglahir : {}".format(e))
    if Tempat.endswith(" "):
        text_dict["Tempat"] = Tempat[:-1]
    else:
        text_dict["Tempat"] = Tempat
    text_dict["TglLahir"] = Tglahir
    text_dict.pop("Tempat/TglLahir")
def select_Jenis(text_dict):
    Jenis_Kelamin = text_dict["Jenis Kelamin"].split("+")
    if len(Jenis_Kelamin) > 1:
        Jenis_Kelamin[0] = re.sub('[^-A-Za-z/. ]+', '', Jenis_Kelamin[0])
        Jenis_Kelamin[1] = re.sub('[^-A-Za-z/. ]+', '', Jenis_Kelamin[1])
        if len(re.sub('[^A-Z]+', '', Jenis_Kelamin[0])) > len(re.sub('[^A-Z]+', '', Jenis_Kelamin[1])):
            text_dict["Jenis Kelamin"] = judge_starts_with(Jenis_Kelamin[0])
        else:
            text_dict["Jenis Kelamin"] = judge_starts_with(Jenis_Kelamin[1])
    else:
        b = re.sub('[^-A-Za-z/. ]+', '', Jenis_Kelamin[0])
        a = maybe_without(b)
        index = len(re.sub('[^-A-Za-z/. ]+', '', a))
        text_dict["Jenis Kelamin"] = judge_starts_with(b[-index:])
def select_Alamat(text_dict):
    Alamat = text_dict["Alamat"].split("+")
    if len(Alamat) > 1:
        Alamat[0] = re.sub('[^-A-Za-z0-9/. ]+', '', Alamat[0])
        Alamat[1] = re.sub('[^-A-Za-z0-9/. ]+', '', Alamat[1])
        if len(re.sub('[^A-Z]+', '', Alamat[0])) > len(re.sub('[^A-Z]+', '', Alamat[1])):
            text_dict["Alamat"] = judge_starts_with(Alamat[0])
        else:
            text_dict["Alamat"] = judge_starts_with(Alamat[1])
    else:
        b = re.sub('[^-A-Za-z0-9/. ]+', '', Alamat[0])
        a = maybe_without(b)
        index = len(re.sub('[^-A-Z0-9/. ]+', '', a))
        text_dict["Alamat"] = judge_starts_with(b[-index:])
def select_RT_RW(text_dict):
    RT_RW = text_dict["RT/RW"]
    temp = re.sub('[^0-9]+', "", RT_RW)
    text_dict["RT"] = temp[0:3]
    text_dict["RW"] = temp[-3:]
    text_dict.pop("RT/RW")
def select_Kel_Desa(text_dict):
    Kel_Desa = text_dict["Kel/Desa"].split("+")
    if len(Kel_Desa) > 1:
        Kel_Desa[0] = re.sub('[^A-Z ]+', '', Kel_Desa[0])
        Kel_Desa[1] = re.sub('[^A-Z ]+', '', Kel_Desa[1])
        if len(Kel_Desa[0]) > len(Kel_Desa[1]):
            text_dict["Kel/Desa"] = judge_starts_with(Kel_Desa[0])
        else:
            text_dict["Kel/Desa"] = judge_starts_with(Kel_Desa[1])
    else:
        b = re.sub('[^A-Za-z ]+', '', Kel_Desa[0])
        a = maybe_without(b)
        index = len(re.sub('[^A-Z ]+', '', a))
        text_dict["Kel/Desa"] = judge_starts_with(b[-index:])
def select_Kecamatan(text_dict):
    Kecamatan = text_dict["Kecamatan"].split("+")
    if len(Kecamatan) > 1:
        Kecamatan[0] = re.sub('[^A-Z ]+', '', Kecamatan[0])
        Kecamatan[1] = re.sub('[^A-Z ]+', '', Kecamatan[1])
        if len(Kecamatan[0]) > len(Kecamatan[1]):
            text_dict["Kecamatan"] = judge_starts_with(Kecamatan[0])
        else:
            text_dict["Kecamatan"] = judge_starts_with(Kecamatan[1])
    else:
        b = re.sub('[^A-Za-z/. ]+', '', Kecamatan[0])
        a = maybe_without(b)
        index = len(re.sub('[^A-Z ]+', '', a))
        text_dict["Kecamatan"] = judge_starts_with(b[-index:])
def select_Agama(text_dict):
    Agama = text_dict["Agama"].split("+")
    if len(Agama) > 1:
        a = re.sub('[^A-Z]+', '', Agama[0])
        b = re.sub('[^A-Z]+', '', Agama[1])
        if len(a) > len(b):
            text_dict["Agama"] = judge_starts_with(a)
        else:
            text_dict["Agama"] = judge_starts_with(b)
    else:
        b = re.sub('[^A-Za-z ]+', '', Agama[0])
        a = maybe_without(b)
        index = len(re.sub('[^A-Z ]+', '', a))
        text_dict["Agama"] = judge_starts_with(b[-index:])

def select_Status_Perkawinan(text_dict):
    labels = ["BELUM KAWIN", "CERAI HIDUP", "CERAI MATI", "KAWIN"]
    Status_Perkawinan = text_dict["Status Perkawinan"]
    temp = re.sub('[^A-Z]+', '', Status_Perkawinan).replace("S", "")
    index_list = []
    for label in labels:
        index_list.append(difflib.SequenceMatcher(None, temp, label).quick_ratio())
    index = index_list.index(max(index_list))
    text_dict["Status Perkawinan"] = labels[index]

def select_Pekerjaan(text_dict):
    Pekerjaan = text_dict["Pekerjaan"].split("+")
    if len(Pekerjaan) > 1:
        a = re.sub('[^A-Z/.() ]+', '', Pekerjaan[0])
        b = re.sub('[^A-Z/.() ]+', '', Pekerjaan[1])
        if len(a) > len(b):
            text_dict["Pekerjaan"] = judge_starts_with(a)
        else:
            text_dict["Pekerjaan"] = judge_starts_with(b)
    else:
        b = re.sub('[^A-Za-z/.() ]+', '', Pekerjaan[0])
        a = maybe_without(b)
        index = len(re.sub('[^A-Z ]+', '', a))
        text_dict["Pekerjaan"] = judge_starts_with(b[-index:])
def select_Kewarga_negaraan(text_dict):
    text_dict["Kewarganegaraan"] = "WNI"
def select_Beriaku_Hingga(text_dict):
    text_dict["Beriaku Hingga"] = "SEUMUR HIDUP"
    """
    Beriaku_Hingga = text_dict["Beriaku Hingga"].split("+")
    if len(Beriaku_Hingga) > 1:
        a = re.sub('[^A-Z/. ]+', '', Beriaku_Hingga[0])
        b = re.sub('[^A-Z/. ]+', '', Beriaku_Hingga[1])
        if len(a) > len(b):
            text_dict["Beriaku Hingga"] = judge_starts_with(a)
        else:
            text_dict["Beriaku Hingga"] = judge_starts_with(b)
    else:
        b = re.sub("[^A-Za-z ]+", "", Beriaku_Hingga[0])
        a = maybe_without(b)
        index = len(re.sub('[^A-Z ]+', '', a))
        text_dict["Beriaku Hingga"] = judge_starts_with(b[-index:])
    """


def refine_labels(result_dict):
    select_PROVINSI(result_dict)
    select_NIK(result_dict)
    select_Nama(result_dict)
    select_Tempat(result_dict)
    select_Jenis(result_dict)
    select_Alamat(result_dict)
    select_RT_RW(result_dict)
    select_Kel_Desa(result_dict)
    select_Kecamatan(result_dict)
    select_Agama(result_dict)
    select_Status_Perkawinan(result_dict)
    select_Pekerjaan(result_dict)
    select_Kewarga_negaraan(result_dict)
    select_Beriaku_Hingga(result_dict)
    return result_dict


def extract_content(texts):  # 先按排序抽取、没有抽取的？？？？
    result_dict = {
        "PROVINSI": "", "City": "", "NIK": "", "Nama": "", "Tempat/TglLahir": "",
        "Jenis Kelamin": "", "Alamat": "", "RT/RW": "", "Kel/Desa": "", "Kecamatan": "",
        "Agama": "", "Status Perkawinan": "", "Pekerjaan": "", "Kewarganegaraan": "",
        "Beriaku Hingga": ""
    }
    merge_next_inf(result_dict, texts)
    refine_labels(result_dict)
    return result_dict


def main(boxes, rec_res, threshold=0.7):
    texts = []
    new_boxes = []
    threshold_for_bottom_picture = boxes[3][1][0] - 5
    for box, rec in zip(boxes, rec_res):
        pre_top_left_height = box[0][0]
        if rec[1] < threshold:
            continue
        if threshold_for_bottom_picture < pre_top_left_height:
            continue
        if difflib.SequenceMatcher(None, rec[0], "Gol.Darah").quick_ratio() > 0.47:
            continue
        if len(rec[0]) < 3:
            continue
        texts.append(rec[0])
        new_boxes.append(box)
    text_box = integrate_picture_boxes(new_boxes, texts)
    print(json.dumps(text_box, indent=1))
    return text_box


if __name__ == "__main__":
    String = "sdf we2f DF2"
    a = re.sub('[^A-Za-z0-9 ]+', '', String)  # 删除符号保留空格
    print(a)
    String = "RT/RW"
    print(difflib.SequenceMatcher(None, "WNI", "FGDf NYBS").quick_ratio())
    Strings = "fdse /TDFVase/ .f .ASDXAEFasdwq"
    print(maybe_without(Strings))
    strings = "HELLO WORLD/DFE . DDEE"
    print(strings.isupper())
    strings = "1920-10-21 a.5/56fe :c35*^#dcxv"
    print(re.sub('[^-A-Za-z0-9/. ]+', '', strings))



