#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import codecs
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


BACKUP_DIR_NAME = ".efmi_unified_backups"
BACKUP_MANIFEST = "manifest.json"
DISABLED_PREFIX = "DISABLED"
OLD_BACKUP_NAME_RE = re.compile(r"\.ini\.backup\.\d{8}_\d{6}$", re.IGNORECASE)
FIXMENU_OLD_TOKEN = "ps-t102"
FIXMENU_NEW_TOKEN = "ps-t100"
MODS_DIR_NAME = "Mods"
HOTFIX_INI_NAME = "EndfieldV1_3Hotfix.ini"
LEGACY_EFMI_SOURCE = "EFMI_Fix_F.py backup marker"
LEGACY_ENDFIELD_SOURCE = "endfield_mod_fix.py marker"
LEGACY_PS_T_SOURCE = "ps_t_shift.py DISABLED backup marker"
LEGACY_PS_T_LINE_SOURCE = "legacy ps-t-shifted marker"
SILENT_STAGE_NAMES = {"legacy_marker_cleanup"}


CHARACTERS = [
    {
        "name": "Perlica",
        "components": [
            { "index": 0, "ib": ("11a44be4", "614a8c60"), "vb0": ("9b882a13", "54a465e3"), "lod_ib": (None, "df4b620c"),       "lod_vb0": ("7d6f86c1", "9eebb5fa"),  "index_count": 45003, "lod_index_count": 23364 },
            { "index": 1, "ib": ("0ccedfdc", "b9767716"), "vb0": ("48e5c5f7", "09e5bc66"), "lod_ib": (None, None)      ,       "lod_vb0": (None,       "c146c65e"),  "index_count":  9186, "lod_index_count": None   },
            { "index": 2, "ib": ("58dc4be7", "ced53e5a"), "vb0": ("5104e6f9", "62bbf2f1"), "lod_ib": ("d232d9c4", "ba2c2cf1"), "lod_vb0": ("0be8a990", "74e93f26"),  "index_count":  5922, "lod_index_count":  4818 },
            { "index": 3, "ib": ("a487adf4", "e7022b54"), "vb0": ("51cf3124", "018e12c8"), "lod_ib": (None, None)      ,       "lod_vb0": (None, None),              "index_count":   525, "lod_index_count": None   },
            { "index": 4, "ib": ("16714b61", "28847e3b"), "vb0": ("8bfe4984", "a8ebf695"), "lod_ib": ("e135fbbc", "2c6dac7e"), "lod_vb0": ("97eb83dd", "5f4fb789"),  "index_count": 78186, "lod_index_count": 34161 },
            { "index": 9, "ib": ("c450a971", "80252467"), "vb0": ("226bfd16", "2f55c2af"), "lod_ib": ("be0e9a56", "859e2f34"), "lod_vb0": ("6c62c480", "099fbd9c"),  "index_count":  2178, "lod_index_count":   891 },
            { "index": 5, "ib": ("e25c17b5", "f4f4158a"), "vb0": ("be81e8e5", "f8059a3b"), "lod_ib": (None, "f4f4158a"),       "lod_vb0": ("c09b9684", "68b0148a"),  "index_count":   480, "lod_index_count":   480 },
            { "index": 7, "ib": ("beeb03c9", "5eeb63d5"), "vb0": ("638fbbea", "54f3754b"), "lod_ib": ("c34ad2e7", "d2745ee4"), "lod_vb0": ("bf7122f7", "b31bc449"),  "index_count": 70656, "lod_index_count": 41022 },
            { "index": 8, "ib": ("ee4a5da9", "40e3cc9b"), "vb0": ("9810da22", "d297fe1e"), "lod_ib": ("8f92dd79", "b03ae6b4"), "lod_vb0": ("a5f6486a", "2db06eb7"),  "index_count":  8460, "lod_index_count":  4986 },
        ]
    },
    {
        "name": "Akekuri",
        "components": [
            { "index": 0, "ib": ("d61b2b27", "a536a1d4"), "vb0": ("aa4613a2", "2950b2f2"), "lod_ib": ("05be7062", "e3eb0556"), "lod_vb0": ("31385163", "28076aa2"), "index_count":2862    , "lod_index_count":1770 },
            { "index": 1, "ib": ("a7a1dfcc", "3623994e"), "vb0": ("8e5fcfc7", "4e680137"), "lod_ib": ("5ebc3af5", "dc4ca03e"), "lod_vb0": ("ab196dbc", "648b2031"), "index_count":41901   , "lod_index_count":29394},
            { "index": 2, "ib": ("785afadb", "809f7872"), "vb0": ("ce63e7f1", "e43f1780"), "lod_ib": ("14699f00", "0090cda2"), "lod_vb0": ("7dfcc640", "06ca0399"), "index_count":114840  , "lod_index_count":68469},
            { "index": 3, "ib": ("04a34e3f", "d021691b"), "vb0": ("d9bbfb78", "43619f7d"), "lod_ib": (None, "db95a416")      , "lod_vb0": ("beae2593", "0fd555a9"), "index_count":9978    , "lod_index_count":9858 },
            { "index": 4, "ib": ("09e21ebc", "277e6c33"), "vb0": ("c5bc9e66", "6786561b"), "lod_ib": ("b1a0de1d", "11b54774"), "lod_vb0": ("484f1dc9", "88280e64"), "index_count":12762   , "lod_index_count":9486 },
            { "index": 5, "ib": ("70254452", "80fa45c6"), "vb0": ("1965d533", "27861764"), "lod_ib": (None, "80fa45c6")      , "lod_vb0": ("1965d533", "27861764"), "index_count":198     , "lod_index_count":198  },
            { "index": 6, "ib": ("21cf8a36", "4f803b00"), "vb0": ("e3ee3b47", "457c72f1"), "lod_ib": (None, "4f803b00")      , "lod_vb0": ("e3ee3b47", "457c72f1"), "index_count":1356    , "lod_index_count":1356 },
            { "index": 7, "ib": ("aa2310ca", "d0555f65"), "vb0": ("9c39e0dc", "01209356"), "lod_ib": (None, None)            , "lod_vb0": (None, None),             "index_count":840     , "lod_index_count":None },
            { "index": 9, "ib": ("c622ce08", "29f01156"), "vb0": ("94ad935a", "1c3c21a7"), "lod_ib": (None, "29f01156")      , "lod_vb0": ("94ad935a", "1c3c21a7"), "index_count":315     , "lod_index_count":315  },
        ]
    },
    {
        "name": "Gilberta",
        "components": [
            { "index": 0, "ib": ("fd5db625", "80402392"), "vb0": ("241cf96e", "2ce6ca0d"), "lod_ib": ("1ce601da", "8c388861"), "lod_vb0": ("a68f8334", "00798620"), "index_count":65130   , "lod_index_count":28863},
            { "index": 1, "ib": ("b7fed652", "959671a1"), "vb0": ("43e0b975", "e574a2b3"), "lod_ib": (None, "26443dcd"),       "lod_vb0": ("c688e896", "3b2de536"), "index_count":7080    , "lod_index_count":3945 },
            { "index": 2, "ib": ("e4919f42", "8c41c63c"), "vb0": ("73f3f4ff", "caac5574"), "lod_ib": ("e1915037", "e8b8a8db"), "lod_vb0": ("0f2f06d1", "29af9eba"), "index_count":167442  , "lod_index_count":51567},
            { "index": 3, "ib": ("07d03512", "581e7b5f"), "vb0": ("14befcdb", "e8c87f40"), "lod_ib": (None, "578b64e2"),       "lod_vb0": ("4af2f36a", "1daeb4e7"), "index_count":8040    , "lod_index_count":8016 },
            { "index": 4, "ib": ("5e662640", "45d0a280"), "vb0": ("ce69fd35", "d13aa1b8"), "lod_ib": (None, None)      ,       "lod_vb0": (None, None),             "index_count":639     , "lod_index_count":None },
            { "index": 5, "ib": ("dd0a3cdc", "6b5e1690"), "vb0": ("fb2cf167", "8f73da0e"), "lod_ib": (None, "6b5e1690"),       "lod_vb0": ("fb2cf167", "8f73da0e"), "index_count":1092    , "lod_index_count":1092 },
            { "index": 6, "ib": ("646957a8", "2eb37e43"), "vb0": ("45dfd165", "a4b54200"), "lod_ib": (None, None)      ,       "lod_vb0": (None, None),             "index_count":1452    , "lod_index_count":None },
            { "index": 8, "ib": ("c6ea4a5e", "7233c71a"), "vb0": ("bcfc5c96", "d508b762"), "lod_ib": ("7fd3cce3", "46e229e8"), "lod_vb0": ("88692db2", "bf1654a4"), "index_count":6123    , "lod_index_count":3081 },
        ]
    },
    {
        "name": "Last Rite",
        "components": [
            { "index": 0 , "ib": ("6360a178", "1f3349f0"), "vb0": ("86fe0853", "9ced068c"), "lod_ib": ("54cf0943", "72a49f78"), "lod_vb0": ("07880af4", "0692f7e2"), "index_count":65007   , "lod_index_count":23694},
            { "index": 1 , "ib": ("79e9d4b2", "6f8b37e5"), "vb0": ("572f0219", "95596155"), "lod_ib": ("ba493804", "6ce07f59"), "lod_vb0": ("84955619", "c6e73ae4"), "index_count":114765  , "lod_index_count":41892},
            { "index": 2 , "ib": ("c1704f73", "ce03a49a"), "vb0": ("580b559e", "18036d7f"), "lod_ib": (None, "2ba325f7")      , "lod_vb0": ("b2e20717", "8cf148ed"), "index_count":48108   , "lod_index_count":23448},
            { "index": 3 , "ib": ("4b912073", "e1127a18"), "vb0": ("4dfadf17", "72c51af1"), "lod_ib": (None, "e1127a18")      , "lod_vb0": ("5b753681", "cd94fdba"), "index_count":10482   , "lod_index_count":10482},
            { "index": 4 , "ib": ("569f9911", "047d6e11"), "vb0": ("862406ce", "84a8b8a1"), "lod_ib": ("f087eba3", "293cb5fa"), "lod_vb0": ("4c2e9e07", "271e5923"), "index_count":3978    , "lod_index_count":1911 },
            { "index": 5 , "ib": ("eb847bab", "48dbb384"), "vb0": ("20b78b5c", "2c45ca79"), "lod_ib": (None, "d8f42f97")      , "lod_vb0": ("af2c5fad", "b884c1a2"), "index_count":453     , "lod_index_count":321  },
            { "index": 6 , "ib": ("b6370970", "42d1cf4a"), "vb0": ("013d84a4", "931ac65d"), "lod_ib": (None, None)            , "lod_vb0": (None, None), "index_count":2748                , "lod_index_count":None },
            { "index": 7 , "ib": ("92bbb63b", "4941de8c"), "vb0": ("643bba47", "3d81aeaa"), "lod_ib": (None, None)            , "lod_vb0": (None, None), "index_count":870                 , "lod_index_count":None },
            { "index": 9 , "ib": ("c3015ab9", "e94e5d43"), "vb0": ("c766d4ea", "59d3f2c0"), "lod_ib": (None, "448d0e1f")      , "lod_vb0": ("a355b8b0", "69cdbd23"), "index_count":966     , "lod_index_count":342  },
            { "index": 10, "ib": ("56865e46", "497764f1"), "vb0": ("f8fef942", "498ef197"), "lod_ib": (None, "e1c41037")      , "lod_vb0": ("ce2297af", "7c2cd0e9"), "index_count":1911    , "lod_index_count":909  },
            { "index": 11, "ib": ("723fa5f9", "19d3babe"), "vb0": ("89b7161b", "06467123"), "lod_ib": (None, "0e81dd4f")      , "lod_vb0": ("56e4432d", "b342d199"), "index_count":4056    , "lod_index_count":1098 },
        ]
    },
    {
        "name": "Laevatain",
        "textures": [
        ("9742a9bb", "990bda3e"),
        ("1a097eaf", "57cf3da0"),
        ],
        "components": [
            { "index": 0 , "ib": ("87ef5d44", "6ec0fbe0"), "vb0": ("642e1067", "fbf42e0a"), "lod_ib": (None, "59107a00"), "lod_vb0": ("730a118e", "ad60d668"), "index_count": 102927,"lod_index_count": 37836 },
            { "index": 1 , "ib": ("49797365", "db438d56"), "vb0": ("e3c1b9d5", "226e96b6"), "lod_ib": (None, "4cfb0d44"), "lod_vb0": ("e7be5c33", "9277fc62"), "index_count": 43044, "lod_index_count": 29655 },
            { "index": 2 , "ib": ("052ebc24", "25937878"), "vb0": ("67915f68", "54052340"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count": 8718,  "lod_index_count": None  },
            { "index": 3 , "ib": ("af73a9d6", "047e538d"), "vb0": ("1234bac3", "cca7b523"), "lod_ib": (None, "98212839"), "lod_vb0": ("703e090d", "2c9489ae"), "index_count": 17337, "lod_index_count": 6678  },
            { "index": 4 , "ib": ("242c74a8", "505d3f14"), "vb0": ("9089f3c7", "22b50c7f"), "lod_ib": (None, "ff514876"), "lod_vb0": ("a7589d8c", "d0a24108"), "index_count": 444,   "lod_index_count": 387   },
            { "index": 5 , "ib": ("54ad754c", "92a32307"), "vb0": ("28670b85", "e6611b04"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count": 948,   "lod_index_count": None  },
            { "index": 7 , "ib": ("c36fba9d", "b64211a7"), "vb0": ("3042d372", "9ee0d4cd"), "lod_ib": (None, "8ce1712c"), "lod_vb0": ("165a7e30", "28fb7c84"), "index_count": 21489, "lod_index_count": 6876  },
            { "index": 8 , "ib": ("c940650c", "737e7030"), "vb0": ("c5d9f9f1", "8d1f3661"), "lod_ib": (None, "68fc2fef"), "lod_vb0": ("5388f608", "921b93b2"), "index_count": 61923, "lod_index_count": 16953 },
            { "index": 9 , "ib": ("17328e5b", "4d91cc2a"), "vb0": ("4868950b", "e5904add"), "lod_ib": (None, "6f8bd031"), "lod_vb0": ("37d0f1a7", "e6ff44f3"), "index_count": 10698, "lod_index_count": 3582  },
            { "index": 10, "ib": ("9386ede2", "ccfd364a"), "vb0": ("6bd00587", "a32bddbf"), "lod_ib": (None, "3190d237"), "lod_vb0": ("369dcb4d", "14ad5977"), "index_count": 7698,  "lod_index_count": 4500  },
            { "index": 11, "ib": (None, "90dc49de")      , "vb0": (None, "c64776f8")      , "lod_ib": (None, "90dc49de"), "lod_vb0": (None, "109edc9a"),       "index_count": 1878,  "lod_index_count": 1878  },
        ]
    },
    {
        "name": "Yvonne",
        "components": [
            { "index": 0 , "ib": ("b21b22ac", "586b4574"), "vb0": ("129c6115", "7e4bca65"), "lod_ib": (None, "b7808834"), "lod_vb0": ("562aaf75", "4333918f"), "index_count": 123174, "lod_index_count":  48711 },
            { "index": 1 , "ib": ("c88d3e16", "c0bb7cd6"), "vb0": ("894ff072", "ebad0fc1"), "lod_ib": (None, "0bddef03"), "lod_vb0": ("87aea2c2", "4523af53"), "index_count":  80781, "lod_index_count":  40482 },
            { "index": 2 , "ib": ("b2b243b1", "c3806ef1"), "vb0": ("de7c9d55", "f16bfc48"), "lod_ib": (None, "c3806ef1"), "lod_vb0": ("35afafa3", "2b0ee891"), "index_count":   8322, "lod_index_count":   8322 },
            { "index": 3 , "ib": ("954c210f", "28ab9d1b"), "vb0": ("36135958", "81cebc78"), "lod_ib": (None, "30c8e217"), "lod_vb0": ("7f5fa711", "57d62490"), "index_count":   1158, "lod_index_count":   1044 },
            { "index": 4 , "ib": ("32edd048", "2c3fe540"), "vb0": ("b90b5a71", "2c1dc974"), "lod_ib": (None, "2c3fe540"), "lod_vb0": ("fd0879a9", "21490081"), "index_count":   1572, "lod_index_count":   1572 },
            { "index": 6 , "ib": ("a55afe59", "7091ba4f"), "vb0": ("91ef4221", "1c466a03"), "lod_ib": (None, "e4119ff0"), "lod_vb0": ("3968f2e8", "54165c20"), "index_count":   6252, "lod_index_count":   4560 },
            { "index": 7 , "ib": ("9f387166", "be538c65"), "vb0": ("f4d81d20", "284c8c5e"), "lod_ib": (None, "ea595f84"), "lod_vb0": ("ee562a7c", "a129deb5"), "index_count":   8622, "lod_index_count":   2514 },
            { "index": 8 , "ib": ("ae7aeacc", "06e91fc9"), "vb0": ("298bdf47", "d2fc12cf"), "lod_ib": (None, "82993ed5"), "lod_vb0": ("798a7fba", "caeac549"), "index_count":  20331, "lod_index_count":   6957 },
            { "index": 9 , "ib": ("0cc8e1f5", "d5cc14a2"), "vb0": ("cdb77262", "585ae775"), "lod_ib": (None, "3cdaab07"), "lod_vb0": ("d1bb0db8", "94eb77fd"), "index_count":   6192, "lod_index_count":   3750 },
            { "index": 10, "ib": ("b8b0d19b", "c92ac28c"), "vb0": ("9ee53d35", "e0f2fb60"), "lod_ib": (None, "e94dd587"), "lod_vb0": ("2734a364", "ba9beddd"), "index_count":   1434, "lod_index_count":     42 },
        ]
    },
    {
        "name": "Avywenna",
        "components": [
            { "index": 0, "ib": ("b83fdbe6", "9abe5753"), "vb0": ("141df854", "18da427a"), "lod_ib": ("2927e519", "1bd4c9ac"), "lod_vb0": ("307d51ba", "6bc6bd65"), "index_count": 156945, "lod_index_count": 56931 },
            { "index": 1, "ib": ("f642ef7b", "e7ef04b0"), "vb0": ("52528888", "12740d99"), "lod_ib": (None, "77f137ad")      , "lod_vb0": ("8fba0892", "82cea0d6"), "index_count": 29520, "lod_index_count": 19668 },
            { "index": 2, "ib": ("70610205", "65707feb"), "vb0": ("68be6bf7", "a7652192"), "lod_ib": (None, "65707feb")      , "lod_vb0": ("68be6bf7", "a7652192"), "index_count": 9714, "lod_index_count": 9714 },
            { "index": 3, "ib": ("e1e47303", "ed3741d9"), "vb0": ("66b33fcb", "ae59d736"), "lod_ib": (None, "748eaf27")      , "lod_vb0": ("b90cf634", "26955095"), "index_count": 753, "lod_index_count": 753 },
            { "index": 4, "ib": ("36cdbe99", "fb9de160"), "vb0": ("16e97389", "ec22dc4b"), "lod_ib": (None, None)            , "lod_vb0": (None, None),             "index_count": 1926, "lod_index_count": None   },
            { "index": 5, "ib": ("745de580", "bce6aed9"), "vb0": ("f82ced8e", "6f8609e3"), "lod_ib": (None, None)            , "lod_vb0": (None, None),             "index_count": 1146, "lod_index_count": None   },
            { "index": 7, "ib": ("430a6db7", "22a60235"), "vb0": ("1a8d3bfc", "709a1c2e"), "lod_ib": (None, "22a60235")      , "lod_vb0": ("1a8d3bfc", "709a1c2e"), "index_count": 4554, "lod_index_count": 4554 },
        ]
    },
    {
        "name": "Xaihi",
        "components": [
            { "index": 0 , "ib": ("34b08b7f", "007cfd9c"), "vb0": ("3de0201b", "64ee5ff5"), "lod_ib": ("b7746d3d", "f8c62748"), "lod_vb0": ("ea8b05de", "e3ae4f48"), "index_count":97986   , "lod_index_count":54216},
            { "index": 1 , "ib": ("000fe31a", "bfd4094f"), "vb0": ("fa25a9d5", "d479eee6"), "lod_ib": ("93dfd264", "41611c0e"), "lod_vb0": ("4d1a8aa8", "ab1cc5de"), "index_count":17067   , "lod_index_count":16203},
            { "index": 2 , "ib": ("951d08b8", "b6e1ea25"), "vb0": ("ca740308", "b1439419"), "lod_ib": (None, "e81bebba"),       "lod_vb0": ("1278845e", "152dc321"), "index_count":8418    , "lod_index_count":8274 },
            { "index": 3 , "ib": ("f34376f4", "e7f5fd02"), "vb0": ("fdaba944", "33a0ab54"), "lod_ib": (None, "e7f5fd02"),       "lod_vb0": ("a154ee18", "33a0ab54"), "index_count":630     , "lod_index_count":630  },
            { "index": 4 , "ib": ("bb9a3863", "681c1f75"), "vb0": ("ee00b22d", "7314a264"), "lod_ib": ("85c3463e", "85c3463e"), "lod_vb0": ("e9778b63", "d6fbf3c8"), "index_count":4962    , "lod_index_count":1545 },
            { "index": 5 , "ib": ("8d99b2df", "d3365100"), "vb0": ("fec42b96", "d2a9f682"), "lod_ib": (None, "7b2af502"),       "lod_vb0": ("616b7f01", "73960c02"), "index_count":1584    , "lod_index_count":1422 },
            { "index": 6 , "ib": ("c82ca4a7", "884c4367"), "vb0": ("f5290f58", "227f9188"), "lod_ib": (None, None)      ,       "lod_vb0": ("9109aad2", None),       "index_count":972     , "lod_index_count":None },
            { "index": 8 , "ib": ("9cbf5b37", "38933272"), "vb0": ("7b3a8e87", "9c4a3b9b"), "lod_ib": ("58ba49c5", "55fb7589"), "lod_vb0": ("6121c920", "c219c834"), "index_count":10236   , "lod_index_count":8235 },
            { "index": 9 , "ib": ("2553dfea", "1d92013a"), "vb0": ("2da2a4d2", "4b108251"), "lod_ib": ("294e15a0", "a0ed1d57"), "lod_vb0": ("cad19f5f", "2b9fa44b"), "index_count":6264    , "lod_index_count":4290 },
            { "index": 10, "ib": ("6b439b09", "84d40040"), "vb0": ("41b261b3", "9eabc128"), "lod_ib": ("2541c8f6", "a36edd49"), "lod_vb0": ("a154ee18", "244d65a6"), "index_count":20964   , "lod_index_count":5697 },
            { "index": 11, "ib": ("93b03b37", "ca878d6d"), "vb0": ("c260b5b6", "6b987e87"), "lod_ib": (None, "74f41773"),       "lod_vb0": ("cba4a0be", "e3e15d6a"), "index_count":1809    , "lod_index_count":885  },
            { "index": 12, "ib": ("114fa06c", "bc3579ff"), "vb0": ("945fe808", "4749d64c"), "lod_ib": (None, "0756d46d"),       "lod_vb0": ("522d908a", "99867fa7"), "index_count":3576    , "lod_index_count":1836 },
        ]
    },
    {
        "name": "Ardelia",
        "components": [
            { "index": 0 , "ib": ("46d6de84", "6bf5c79b"), "vb0": ("d3dfe233", "1fe65d02"), "lod_ib": (None, "f4e599c8"),       "lod_vb0": ("696d36cc", "033e4833"), "index_count": 51789, "lod_index_count": 20451 },
            { "index": 1 , "ib": ("2ee77752", "c8197c5b"), "vb0": ("c997ee07", "37c2a325"), "lod_ib": ("f855fe01", "3d7defd8"), "lod_vb0": ("587d9f6c", "35a2c824"), "index_count": 53472, "lod_index_count": 24768 },
            { "index": 2 , "ib": ("194f3cbe", "b9623e31"), "vb0": ("9d7323e9", "d0514f79"), "lod_ib": ("194f3cbe", "5a0b7cf0"), "lod_vb0": ("38768d69", "30fd597e"), "index_count": 11112, "lod_index_count": 4797  },
            { "index": 3 , "ib": ("0bf2bd32", "36a08ea0"), "vb0": ("b546026b", "8c04f0ec"), "lod_ib": ("68375f0d", "467076b1"), "lod_vb0": ("6d0d1d6a", "dcae32b6"), "index_count": 83514, "lod_index_count": 43773 },
            { "index": 4 , "ib": ("de33606d", "78554d71"), "vb0": ("d9ead4ed", "c68238c7"), "lod_ib": (None, "78554d71"),       "lod_vb0": ("bdefeeda", "40855fca"), "index_count": 9282,  "lod_index_count": 9282  },
            { "index": 5 , "ib": ("ea9dcbd0", "522ef1e3"), "vb0": ("143326ef", "58727a28"), "lod_ib": (None, "1f200672"),       "lod_vb0": ("1ce3c134", "b48706b9"), "index_count": 1614,  "lod_index_count": 540   },
            { "index": 6 , "ib": ("c3ccabdd", "4eae267c"), "vb0": ("820d431f", "804516ad"), "lod_ib": (None, "9736bb8c"),       "lod_vb0": ("86374159", "321fd236"), "index_count": 2598,  "lod_index_count": 2598  },
            { "index": 7 , "ib": ("1d2c1103", "32b98652"), "vb0": ("678659c0", "33415cdb"), "lod_ib": (None, "32b98652"),       "lod_vb0": ("ce148f9b", "871ad7d8"), "index_count": 996,   "lod_index_count": 996   },
            { "index": 9 , "ib": ("278e343e", "d6128f13"), "vb0": ("849156e1", "fafe1257"), "lod_ib": ("5e263243", "c1760cc4"), "lod_vb0": ("8f4c614f", "ee7f0f22"), "index_count": 14664, "lod_index_count": 7596  },
            { "index": 10, "ib": ("bccea385", "0af3ccb1"), "vb0": ("7aa1b27e", "99e483c8"), "lod_ib": (None, "108b0ab1"),       "lod_vb0": ("7dbf91f2", "575c3332"), "index_count": 3780,  "lod_index_count": 1860  },
            { "index": 11, "ib": ("3b18976f", "cc35f7fa"), "vb0": ("c9cda963", "f5a1a32e"), "lod_ib": ("7aabda96", "7e4ccfbf"), "lod_vb0": ("a9e9e302", "30011d25"), "index_count": 2565,  "lod_index_count": 1026  },
            { "index": 12, "ib": ("a2888b1d", "99451bd3"), "vb0": ("c3f10721", "fa748886"), "lod_ib": ("c40c18da", "4532f3b9"), "lod_vb0": ("34409a6a", "c389165f"), "index_count": 3879,  "lod_index_count": 1779  },
        ]
    },
    {
        "name": "Chen Qianyu",
        "components": [
            { "index": 0, "ib": ("1bbe6c57", "f80227f2"), "vb0": ("323b8ae3", "9ab25d04"), "lod_ib": ("c7f354a2", "429e5708"), "lod_vb0": ("0210cd02", "c5c96fc9"), "index_count":139392  , "lod_index_count":34362},
            { "index": 1, "ib": ("2d9afada", "7682fa9c"), "vb0": ("4601fc7a", "e1ebcc82"), "lod_ib": (None, "a95b952d"),       "lod_vb0": ("e2bf71f0", "32e69553"), "index_count":46728   , "lod_index_count":37392},
            { "index": 2, "ib": ("adada9dd", "573c7681"), "vb0": ("96a2930e", "e74cb81e"), "lod_ib": (None, "97879a30"),       "lod_vb0": ("5368e59d", "3506f572"), "index_count":714     , "lod_index_count":525  },
            { "index": 3, "ib": ("80b1cab9", "b284ad1e"), "vb0": ("08300f65", "9cc82ad1"), "lod_ib": (None, "b284ad1e"),       "lod_vb0": ("ad1e3949", "190e6a7d"), "index_count":888     , "lod_index_count":888  },
            { "index": 5, "ib": ("072a2083", "d52ade91"), "vb0": ("b8b3e4c1", "05c45be0"), "lod_ib": ("28ce8d60", "a37021ba"), "lod_vb0": ("c568aff9", "852b9e76"), "index_count":4524    , "lod_index_count":1932 },
            { "index": 6, "ib": ("096061db", "ae154b07"), "vb0": ("c4d45493", "e91ce38d"), "lod_ib": ("3731f55b", "fc19ffe3"), "lod_vb0": ("910de677", "edea3bce"), "index_count":9477    , "lod_index_count":5001 },
            { "index": 7, "ib": ("98aa3cf8", "0c94b618"), "vb0": ("3589e82f", "f72e0492"), "lod_ib": (None, "f522aabb"),       "lod_vb0": ("08cf9fbc", "bd1d9644"), "index_count":15138   , "lod_index_count":7140 },
        ]
    },
    {
        "name": "Ember",
        "components": [
            { "index": 0 , "ib": ("bf8073db", "028bdd2a"), "vb0": ("529ab1c9", "a2236f1c"), "lod_ib": (None, "48557ca4"), "lod_vb0": ("b8c35aa2", "e12286cd"), "index_count":99162   , "lod_index_count":57693 },
            { "index": 1 , "ib": ("3424cfb0", "fd10876c"), "vb0": ("2a3d50c3", "bcde2040"), "lod_ib": (None, "3e483a0d"), "lod_vb0": ("e7a48931", "f63dedd1"), "index_count":43362   , "lod_index_count":32481 },
            { "index": 2 , "ib": ("7ad43302", "96da0da8"), "vb0": ("9c2d3f9b", "b00c686a"), "lod_ib": (None, "dd880448"), "lod_vb0": ("a992c6af", "ca503ceb"), "index_count":8502    , "lod_index_count":8502  },
            { "index": 3 , "ib": ("c815a2dc", "9c51fcb7"), "vb0": ("a883cfd7", "983b84c9"), "lod_ib": (None, "eb3b3454"), "lod_vb0": ("bdb8b9b3", "62946b98"), "index_count":366     , "lod_index_count":267   },
            { "index": 4 , "ib": ("211fc0a3", "9f7a91a0"), "vb0": ("017770a8", "d979bdca"), "lod_ib": (None, "10bfdf8d"), "lod_vb0": ("b0d7b4a0", "b8b40b6a"), "index_count":1782    , "lod_index_count":840   },
            { "index": 5 , "ib": ("d896ff2f", "5709a504"), "vb0": ("c7cc6650", "17ff7ab8"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":1434    , "lod_index_count":None  },
            { "index": 6 , "ib": ("24fda00a", "d5a9594f"), "vb0": ("f415f0a3", "b558357d"), "lod_ib": (None, "d5a9594f"), "lod_vb0": ("a821a80e", "355ef6b9"), "index_count":948     , "lod_index_count":948   },
            { "index": 7 , "ib": ("ef01d5c3", "0834e8e4"), "vb0": ("382b8324", "fd2c4fe6"), "lod_ib": (None, "79b78a0f"), "lod_vb0": ("10caf75f", "e0a4d8b2"), "index_count":3138    , "lod_index_count":3132  },
            { "index": 9 , "ib": ("114fce48", "6f299713"), "vb0": ("7a3bb986", "08637f97"), "lod_ib": (None, "ef77087e"), "lod_vb0": ("b75ffc38", "6776629b"), "index_count":41334   , "lod_index_count":18642 },
            { "index": 10, "ib": ("d8b51371", "ed955584"), "vb0": ("3a339bf2", "387617db"), "lod_ib": (None, "b53a5ba8"), "lod_vb0": ("7cc5a3f9", "dffc05fb"), "index_count":3978    , "lod_index_count":1368  },
        ]
    },
    {
        "name": "Fluorite",
        "components": [
            { "index": 0, "ib": ("48741da5", "545dfa3b"), "vb0": ("c21a6d0c", "45d8fba2"), "lod_ib": ("64153b2b", "64153b2b"), "lod_vb0": ("82047422", "c1f6de5d"), "index_count":109017  , "lod_index_count":61299 },
            { "index": 1, "ib": ("4c711941", "8f31d73b"), "vb0": ("a2da5c35", "49bcc725"), "lod_ib": ("29122995", "29122995"), "lod_vb0": ("cc72a970", "99ec6015"), "index_count":27483   , "lod_index_count":13692 },
            { "index": 2, "ib": ("ee799f02", "232d0632"), "vb0": ("f49022e3", "58e1105c"), "lod_ib": (None, None)            , "lod_vb0": (None, None),             "index_count":9762    , "lod_index_count":None  },
            { "index": 3, "ib": ("23c933c3", "e0dc2c31"), "vb0": ("6babe75c", "c140aab2"), "lod_ib": ("210e616b", "210e616b"), "lod_vb0": ("b3e07335", "f6194885"), "index_count":960     , "lod_index_count":714   },
            { "index": 4, "ib": ("65aa49f9", "84c7926d"), "vb0": ("6b0bea53", "3f50da1e"), "lod_ib": ("533b4170", "533b4170"), "lod_vb0": ("7e1baee2", "56147388"), "index_count":1428    , "lod_index_count":1008  },
            { "index": 5, "ib": ("46d61c5f", "8a5e516d"), "vb0": ("15532afa", "662c8188"), "lod_ib": ("06fd20f3", "06fd20f3"), "lod_vb0": ("1c7ce059", "a43ce6e9"), "index_count":12102   , "lod_index_count":11706 },
            { "index": 6, "ib": ("b7f2e2da", "188f975d"), "vb0": ("903f6590", "ce495028"), "lod_ib": ("baccaa6d", "baccaa6d"), "lod_vb0": ("4814850a", "3582f761"), "index_count":31170   , "lod_index_count":18372 },
            { "index": 7, "ib": ("11536e01", "a68526c8"), "vb0": ("7278d2d2", "b47989a5"), "lod_ib": ("1c6d9af6", "1c6d9af6"), "lod_vb0": ("dd318f98", "505bf8dc"), "index_count":78      , "lod_index_count":48    },
            { "index": 8, "ib": (None,       "7a01407e"), "vb0": ("a750c69c",       None), "lod_ib": (None, None)            , "lod_vb0": (None, None),             "index_count":186     , "lod_index_count":None  },
        ]
    },
    {
        "name": "Arclight",
        "components": [
            { "index": 0, "ib": ("03bdaa91", "737f4c35"), "vb0": ("b48d4f24", "67afd93d"), "lod_ib": (None, "86f40ec1"), "lod_vb0": ("9a5f3f06", "df88d775"), "index_count":64533   , "lod_index_count":47643},
            { "index": 1, "ib": ("ac89327d", "2cc316a9"), "vb0": ("e2948ff0", "6659b1d4"), "lod_ib": (None, "5609cf41"), "lod_vb0": ("966e1280", "c2921114"), "index_count":83589   , "lod_index_count":33312},
            { "index": 2, "ib": ("2adcb3e0", "234ff157"), "vb0": ("6dcf3af4", "1dd29c87"), "lod_ib": (None, "6c889b36"), "lod_vb0": ("ce6b117d", "8540587c"), "index_count":8376    , "lod_index_count":8376 },
            { "index": 3, "ib": ("ca3feeba", "97177794"), "vb0": ("078861af", "d0495f16"), "lod_ib": (None, "97177794"), "lod_vb0": ("eee7e9b8", "3082211d"), "index_count":270     , "lod_index_count":270  },
            { "index": 4, "ib": ("65584291", "efaa01a3"), "vb0": ("bd653152", "f3ef0db4"), "lod_ib": (None, "efaa01a3"), "lod_vb0": ("d38a097c", "56c19803"), "index_count":1476    , "lod_index_count":1476 },
            { "index": 5, "ib": ("ad0d1312", "140c048c"), "vb0": ("881c2c14", "595e832d"), "lod_ib": (None, "177e0826"), "lod_vb0": ("f88a043c", "afc1ed6d"), "index_count":9459    , "lod_index_count":5553 },
            { "index": 6, "ib": ("821bc0d1", "04aa4899"), "vb0": ("acba4f73", "45080a4b"), "lod_ib": (None, "04aa4899"), "lod_vb0": ("b77cc591", "9d3fbc09"), "index_count":1152    , "lod_index_count":1152 },
            { "index": 8, "ib": ("a30456fa", "cd8519a8"), "vb0": ("bc26d671", "78b62b4a"), "lod_ib": (None, "957c6dd2"), "lod_vb0": ("1a4a70c0", "b4072d6d"), "index_count":255     , "lod_index_count":117  },
        ]
    },
    {
        "name": "MEndministrator",
        "components": [
            { "index": 0 , "ib": ("64198ffd", "3d9e52b8"), "vb0": ("9c5ef0f2", "912b1f0a"), "lod_ib": (None, "5c29f1fc"), "lod_vb0": ("2d12859c", "b350de12"), "index_count":32772   , "lod_index_count":20247 },
            { "index": 1 , "ib": ("e56aef4c", "3e28fc20"), "vb0": ("4e464997", "99b14bfc"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":17022   , "lod_index_count":None  },
            { "index": 2 , "ib": ("20ecd1f3", "43119cea"), "vb0": ("dcc50645", "64ba13ce"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":9786    , "lod_index_count":None  },
            { "index": 3 , "ib": ("18220d55", "5825df15"), "vb0": ("0bf3c047", "a44dbc25"), "lod_ib": (None, "070d7b84"), "lod_vb0": ("eeb7427b", "123ee378"), "index_count":4524    , "lod_index_count":2028  },
            { "index": 4 , "ib": ("a003e66b", "fec5873f"), "vb0": ("fa905dcf", "57174c28"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":1608    , "lod_index_count":None  },
            { "index": 5 , "ib": ("2b28489c", "92b0136c"), "vb0": ("7f017574", "ab3c72c3"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":1128    , "lod_index_count":None  },
            { "index": 6 , "ib": ("4cd1ad3b", "b1f947ec"), "vb0": ("de099ea0", "485eee8a"), "lod_ib": (None, "2f3d2c97"), "lod_vb0": ("19df7e80", "48f755d5"), "index_count":117     , "lod_index_count":51  },
            { "index": 8 , "ib": ("046d734d", "bf3c08af"), "vb0": ("5b7621ad", "4c0eccb2"), "lod_ib": (None, "3fc2a3de"), "lod_vb0": ("53976979", "b53069cf"), "index_count":20238   , "lod_index_count":13344 },
            { "index": 9 , "ib": ("50c35406", "b3bf2e13"), "vb0": ("3f640f8d", "dc8e72ca"), "lod_ib": (None, "9b189efd"), "lod_vb0": ("be7729b3", "80016419"), "index_count":46437   , "lod_index_count":17052 },
            { "index": 10, "ib": ("78a3d343", "b57bbb30"), "vb0": ("122c46be", "bb2dd9f7"), "lod_ib": (None, "7cdfa2a3"), "lod_vb0": ("9468e4fc", "b991a3bd"), "index_count":69195   , "lod_index_count":27255 },
        ]
    },
    {
        "name": "FEndministrator",
        "components": [
            { "index": 0 , "ib": ("f0e903d9", "638e0992"), "vb0": ("c78283e1", "3c39f250"), "lod_ib": (None, "fc36f44e"), "lod_vb0": ("481b2ac9", "6f9f8f2d"),      "index_count":27615 , "lod_index_count":24939},
            { "index": 1 , "ib": ("b2e8c655", "4eabed4f"), "vb0": ("1061306c", "8ff3e4ee"), "lod_ib": (None, "4eabed4f"), "lod_vb0": (None, "8ff3e4ee"),            "index_count":9000  , "lod_index_count":9000 },
            { "index": 2 , "ib": ("18220d55", "5825df15"), "vb0": ("ba3f54e3", "7dc82d5c"), "lod_ib": (None, "070d7b84"), "lod_vb0": ("04c8dfc2", "1e4e87da"),      "index_count":4524  , "lod_index_count":2028 },
            { "index": 3 , "ib": ("b960f7ad", "827a29bc"), "vb0": ("9b5f1414", "18351da6"), "lod_ib": (None, "e2055625"), "lod_vb0": ("55595ecb", "3bec71fe"),      "index_count":20577 , "lod_index_count":10014},
            { "index": 4 , "ib": ("540c5d1c", "586dadd6"), "vb0": ("a0f67a46", "457bb329"), "lod_ib": (None, "984608e7"), "lod_vb0": ("1dae91af", "8eeba60c"),      "index_count":1638  , "lod_index_count":1638 },
            { "index": 5 , "ib": ("149f97a2", "fa04a7b6"), "vb0": ("484f1dc9", "8443a8df"), "lod_ib": (None, "fa04a7b6"), "lod_vb0": (None, "8443a8df"),            "index_count":16524 , "lod_index_count":None },
            { "index": 6 , "ib": ("4cd1ad3b", "b1f947ec"), "vb0": ("c7fb8d3e", "c965ae7e"), "lod_ib": (None, "c74fffeb"), "lod_vb0": ("f6aa513f", "26d0c0fa"),      "index_count":117   , "lod_index_count":69   },
            { "index": 7 , "ib": ("6fc5eb90", "57f73db4"), "vb0": ("de4df2c4", "8a383186"), "lod_ib": (None, "57f73db4"), "lod_vb0": ("204892e9", "6b1d7b58"),      "index_count":1386  , "lod_index_count":1386 },
            { "index": 9 , "ib": ("cced9603", "9cd919fa"), "vb0": ("e34d63f8", "7b244efc"), "lod_ib": ("8ef1f8f0", "9ba0fdcb"), "lod_vb0": ("47b3e8ee", "8599862c"),"index_count":101994, "lod_index_count":59301},
            { "index": 10, "ib": ("23afb707", "316571b5"), "vb0": ("953431a6", "6e15377c"), "lod_ib": ("e509c003", "38e34aa3"), "lod_vb0": ("79e1a048", "74e74f3e"),"index_count":2286  , "lod_index_count":777  },
        ]
    },
    {
        "name": "Wulfgard",
        "components": [
            { "index": 0 , "ib": ("c8e852f0", "63f7dabd"), "vb0": ("1db5c279", "a0aba97f"), "lod_ib": (None, "05c5fa92"), "lod_vb0": ("8008b084", "1e5e4f05"), "index_count":31197   , "lod_index_count":16014 },
            { "index": 1 , "ib": ("31cd6d7d", "c20ff35c"), "vb0": ("7bbdd220", "10d5b3c2"), "lod_ib": (None, "6954e762"), "lod_vb0": ("584e835b", "a9c5d6a8"), "index_count":2574    , "lod_index_count":1224  },
            { "index": 2 , "ib": ("6958aa51", "d59d4ea2"), "vb0": ("458f6cbc", "fa6cc1c3"), "lod_ib": (None, "85ed9a0b"), "lod_vb0": ("5ecb41e1", "88d19af5"), "index_count":264     , "lod_index_count":258   },
            { "index": 3 , "ib": ("e2fb6d2e", "482eb5e4"), "vb0": ("ac2afb73", "e473eb84"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":10308   , "lod_index_count":None  },
            { "index": 4 , "ib": ("08d6cb6b", "9e85dddf"), "vb0": ("4b1bf48a", "c298c42b"), "lod_ib": (None, "83277d8b"), "lod_vb0": ("b1fc0a4b", "fd1ee6a6"), "index_count":5352    , "lod_index_count":2571  },
            { "index": 5 , "ib": ("8ff1778f", "49e81624"), "vb0": ("380be5fd", "6c30e20c"), "lod_ib": (None, "7fb2be96"), "lod_vb0": ("90410931", "bc3265f1"), "index_count":1410    , "lod_index_count":666   },
            { "index": 6 , "ib": ("e9ff5e96", "84be7d8c"), "vb0": ("1c7bbd4f", "aac8b096"), "lod_ib": (None, "b84e32bf"), "lod_vb0": ("74960856", "3d3e90f0"), "index_count":1080    , "lod_index_count":504   },
            { "index": 8 , "ib": ("8ced708e", "57eaef1a"), "vb0": ("01b51c37", "3af5eb92"), "lod_ib": (None, "2177685d"), "lod_vb0": ("332b19c6", "94dd3e64"), "index_count":16980   , "lod_index_count":8853  },
            { "index": 9 , "ib": ("a6a1af73", "fd763e59"), "vb0": ("204ecd3c", "fae9156a"), "lod_ib": (None, "5f597f6d"), "lod_vb0": ("1b9b9ce4", "4f8c5f42"), "index_count":66558   , "lod_index_count":32775 },
            { "index": 10, "ib": ("b2b4d40d", "1ff0800e"), "vb0": ("faa6aaf1", "67b653e4"), "lod_ib": (None, "593bfaa5"), "lod_vb0": ("c6b0dc35", "ae733e70"), "index_count":75222   , "lod_index_count":33708 },
            { "index": 11, "ib": ("77979b14", "6337aa62"), "vb0": ("e8ee1dc4", "edc6b09f"), "lod_ib": (None, "ea2de3f2"), "lod_vb0": ("3c41e139", "4fa961af"), "index_count":2850    , "lod_index_count":1356  },
            { "index": 12, "ib": ("4b1755ff", "b5d46f1b"), "vb0": ("9f611fa4", "e433e900"), "lod_ib": (None, "5af82d95"), "lod_vb0": ("38f904c6", "d55e0245"), "index_count":1452    , "lod_index_count":528   },
            { "index": 13, "ib": ("feb28fd9", "2ba642cf"), "vb0": ("f386b8a5", "596fba9e"), "lod_ib": (None, "26b0738f"), "lod_vb0": ("1dc396f4", "8bd7d304"), "index_count":3852    , "lod_index_count":1854  },
        ]
    },
    {
        "name": "Antal",
        "components": [
            { "index": 0, "ib": ("f68bf1c3", "bc07b597"), "vb0": ("fc0211d2", "cfc74bc1"), "lod_ib": (None, "58b42909"), "lod_vb0": ("1bef755f", "efda68e0"), "index_count":9948    , "lod_index_count":9330  },
            { "index": 1, "ib": ("8c765dbd", "8e5c67f6"), "vb0": ("3a512b0d", "a3842ef3"), "lod_ib": (None, "5eb23f3c"), "lod_vb0": ("9109aad2", "f02d066a"), "index_count":936     , "lod_index_count":624   },
            { "index": 2, "ib": ("1987be49", "af6aba6c"), "vb0": ("9bfb1586", "0df72e7b"), "lod_ib": (None, "a3893eda"), "lod_vb0": ("697ef901", "c3cb0e13"), "index_count":2430    , "lod_index_count":1248  },
            { "index": 3, "ib": ("24d00869", "dd894994"), "vb0": ("bdbf6182", "e8f44ed3"), "lod_ib": (None, "8a4f2d38"), "lod_vb0": ("7059bd80", "30c8f355"), "index_count":81438   , "lod_index_count":72645 },
            { "index": 4, "ib": ("a16fbb9c", "ff511c12"), "vb0": ("fa09e3d3", "2da68c73"), "lod_ib": (None, "378b6447"), "lod_vb0": ("85236948", "18c48b8a"), "index_count":31872   , "lod_index_count":30135 },
            { "index": 5, "ib": ("5a08dbdf", "7ee52863"), "vb0": ("c1f3e031", "5c17c1e7"), "lod_ib": (None, "9ab2cc71"), "lod_vb0": ("75f764ad", "c15ffce0"), "index_count":8100    , "lod_index_count":5778  },
        ]
    },
    {
        "name": "Alesh",
        "components": [
            { "index": 0 , "ib": ("bef98f14", "d9f9149d"), "vb0": ("519d9ad9", "ddc34665"), "lod_ib": (None, "d149d9e9"), "lod_vb0": ("c6b94298", "dd0731f3"), "index_count":38520   , "lod_index_count":18987 },
            { "index": 1 , "ib": ("b6d7d2c5", "00532aa6"), "vb0": ("41e695ff", "1dc688e2"), "lod_ib": (None, "58a61a76"), "lod_vb0": ("02ff51bb", "18d4f253"), "index_count":125835  , "lod_index_count":70572 },
            { "index": 2 , "ib": ("b2268feb", "8b6961fa"), "vb0": ("8f0a8053", "596c5ca9"), "lod_ib": (None, "f67ae5c2"), "lod_vb0": ("91cbefde", "083e40d3"), "index_count":2460    , "lod_index_count":1224  },
            { "index": 3 , "ib": ("a85fdd50", "309d81d3"), "vb0": ("efc0109f", "5c1364f6"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":435     , "lod_index_count":None  },
            { "index": 4 , "ib": ("a10114f6", "c59e0bbd"), "vb0": ("4769edc8", "f54c0c9f"), "lod_ib": (None, "6efced3d"), "lod_vb0": ("4d712603", "ec229f78"), "index_count":12210   , "lod_index_count":12210 },
            { "index": 5 , "ib": ("a52d4d84", "bcf74f8e"), "vb0": ("9c840c4b", "e8e04ebb"), "lod_ib": (None, "1a65ce37"), "lod_vb0": ("63464f5a", "d597fb72"), "index_count":1866    , "lod_index_count":1776  },
            { "index": 6 , "ib": ("1bd99496", "218c9f50"), "vb0": ("97da5e0f", "730efd38"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":1320    , "lod_index_count":None  },
            { "index": 7 , "ib": ("63703f1f", "057b76e4"), "vb0": ("23858a76", "d4f132fd"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":816     , "lod_index_count":None  },
            { "index": 9 , "ib": ("c6f40179", "6985f42b"), "vb0": ("957fa732", "665ea4ca"), "lod_ib": (None, "6985f42b"), "lod_vb0": ("b31849d3", "ab6ee574"), "index_count":1080    , "lod_index_count":1080  },
            { "index": 10, "ib": ("378f5e3f", "e3ecf416"), "vb0": ("9445d9e4", "8dce615a"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":2196    , "lod_index_count":None  },
        ]
    },
    {
        "name": "Estella",
        "components": [
            { "index": 0, "ib": ("d90916ab", "0f670f77"), "vb0": ("e134baae", "a207af4a"), "lod_ib": (None, "3c12d828"), "lod_vb0": ("ef87e30b", "745b9e9c"), "index_count":111693  , "lod_index_count":71076},
            { "index": 1, "ib": ("962a8945", "fa0d4a01"), "vb0": ("93085821", "bd9d7e11"), "lod_ib": (None, "4293dd55"), "lod_vb0": ("3cb7bf32", "79314392"), "index_count":1500    , "lod_index_count":1095 },
            { "index": 2, "ib": ("d4b6cc47", "06e98976"), "vb0": ("16462a40", "479aabe4"), "lod_ib": (None, "06e98976"), "lod_vb0": (None, "479aabe4"),       "index_count":11370   , "lod_index_count":11370},
            { "index": 3, "ib": ("c2e56891", "0b2ddd81"), "vb0": ("ec2e0458", "7d37958f"), "lod_ib": (None, "b700d0c3"), "lod_vb0": ("39dc3c86", "ddcd21fe"), "index_count":16539   , "lod_index_count":11979},
            { "index": 4, "ib": ("e839faab", "7fa97135"), "vb0": ("7c872134", "eacecd4b"), "lod_ib": (None, "a3375e8b"), "lod_vb0": ("14dcc267", "25bb7414"), "index_count":32529   , "lod_index_count":20676},
            { "index": 5, "ib": ("523526f7", "fb2b7bd9"), "vb0": ("c6a37bfa", "a1a6ee38"), "lod_ib": (None, "df7f2f03"), "lod_vb0": ("3b751e79", "ec9359b2"), "index_count":441     , "lod_index_count":423  },
            { "index": 6, "ib": ("427bad30", "2deb826c"), "vb0": ("395dd7fd", "09c5e965"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":1692    , "lod_index_count":None },
            { "index": 7, "ib": ("effcbd48", "652780a2"), "vb0": ("0992a523", "40eea6a9"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":1128    , "lod_index_count":None },
            { "index": 9, "ib": ("358d5b42", "7d15098a"), "vb0": ("c1705d7e", "53bbede7"), "lod_ib": (None, "54f03f79"), "lod_vb0": ("4740c7d4", "3dd4db42"), "index_count":669     , "lod_index_count":411  },
        ]
    },
    {
        "name": "Snowshine",
        "components": [
            { "index": 0, "ib": ("bbecc467", "9b331c41"), "vb0": ("2d57302c", "f4fdbff9"), "lod_ib": (None, None), "lod_vb0": ("1417d5fd", None), "index_count":32832   , "lod_index_count":6426     },
            { "index": 1, "ib": ("aa6c983f", "7cca4f82"), "vb0": ("a631905d", "828cf859"), "lod_ib": (None, None), "lod_vb0": ("9a2dea62", None), "index_count":25470   , "lod_index_count":18654    },
            { "index": 2, "ib": ("812e1486", "b4310e71"), "vb0": ("0bf9550d", "6b0e0aeb"), "lod_ib": (None, None), "lod_vb0": ("a4ca29cc", None), "index_count":73359   , "lod_index_count":36441    },
            { "index": 3, "ib": ("3281f879", "d133ae20"), "vb0": ("46ad3467", "e77948ae"), "lod_ib": (None, None), "lod_vb0": ("a677fc0e", None), "index_count":5262    , "lod_index_count":2418     },
            { "index": 4, "ib": ("5f3890fd", "b144d4cd"), "vb0": ("8a94fc99", "44939509"), "lod_ib": (None, None), "lod_vb0": ("0ecd8dab", None), "index_count":9012    , "lod_index_count":9012     },
            { "index": 5, "ib": ("cbfbbf15", "dadf5a1f"), "vb0": ("f8f8b873", "7ddc9e9c"), "lod_ib": (None, None), "lod_vb0": ("916e8733", None), "index_count":7659    , "lod_index_count":3939     },
            { "index": 6, "ib": ("02010e21", "a4dc0ce9"), "vb0": ("b7085b91", "b5063f88"), "lod_ib": (None, None), "lod_vb0": ("160a5f97", None), "index_count":1476    , "lod_index_count":1128     },
            { "index": 7, "ib": ("b921120f", "020075ae"), "vb0": ("2a040db9", "57e0a670"), "lod_ib": (None, None), "lod_vb0": ("f961e9f2", None), "index_count":2088    , "lod_index_count":2088     },
            { "index": 8, "ib": ("f7793e31", "6a2a6d0b"), "vb0": ("a0988be6", "17bb3c35"), "lod_ib": (None, None), "lod_vb0": ("8962b34c", None), "index_count":1224    , "lod_index_count":1224     },
            { "index": 9, "ib": ("5035c203", "0671628a"), "vb0": ("bdbb8a49", "381dfded"), "lod_ib": (None, None), "lod_vb0": ("26164c46", None), "index_count":87120   , "lod_index_count":43476    },
        ]
    },
    {
        "name": "Pogranichnik",
        "components": [
            { "index": 0 , "ib": ("f9f4e1c5", "c8456b2c"), "vb0": ("0e300723", "57a90575"), "lod_ib": (None, "97fdc630"), "lod_vb0": ("f411ca40", "f1fb782d"), "index_count":7530    , "lod_index_count":3408 },
            { "index": 1 , "ib": ("7d1bfb62", "e2a33da1"), "vb0": ("3387235b", "204852a3"), "lod_ib": (None, "270a5969"), "lod_vb0": ("4ce6c32c", "d9072a30"), "index_count":49941   , "lod_index_count":24030},
            { "index": 2 , "ib": ("15577b66", "245c0cd3"), "vb0": ("72fac41f", "11e5717d"), "lod_ib": (None, "56ff3728"), "lod_vb0": ("470ec441", "2e226ecd"), "index_count":112620  , "lod_index_count":44139},
            { "index": 3 , "ib": ("d5a4cbc0", "55359cb8"), "vb0": ("ae8cde6d", "1cd96ce5"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":11346   , "lod_index_count":None },
            { "index": 4 , "ib": ("86530b9b", "76d2249e"), "vb0": ("6e06ce7c", "31f2904a"), "lod_ib": (None, "834dd8e1"), "lod_vb0": ("3464a68c", "a8f724c7"), "index_count":1614    , "lod_index_count":966  },
            { "index": 5 , "ib": ("732041d6", "ba09e595"), "vb0": ("acc1b61a", "d48dc9d8"), "lod_ib": (None, "ba09e595"), "lod_vb0": ("acc1b61a", "d48dc9d8"), "index_count":1926    , "lod_index_count":1926 },
            { "index": 6 , "ib": ("718f6aa0", "14a888b5"), "vb0": ("2c75375a", "1c09cea1"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":876     , "lod_index_count":None },
            { "index": 7 , "ib": ("27c008a2", "d3724664"), "vb0": ("c47043a4", "90d305a3"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":102     , "lod_index_count":None },
            { "index": 8 , "ib": ("8ad8694a", "dc206164"), "vb0": ("55f2b0d8", "9e2b7c13"), "lod_ib": (None, "27e5080a"), "lod_vb0": ("32510aaa", "6ed66b29"), "index_count":2706    , "lod_index_count":831  },
            { "index": 9 , "ib": ("891a21b7", "77990575"), "vb0": ("fcfd273f", "1321c025"), "lod_ib": (None, "e7b67ff7"), "lod_vb0": ("c62e1d3a", "a2e0d754"), "index_count":77412   , "lod_index_count":26439},
            { "index": 10, "ib": ("b3afd814", "daa8697b"), "vb0": ("d02d389c", "0fb85414"), "lod_ib": (None, "bc915bd9"), "lod_vb0": ("e86c895a", "2b3e232a"), "index_count":8229    , "lod_index_count":3735 },
            { "index": 11, "ib": ("a2b13205", "ee8e48c2"), "vb0": ("27f3371b", "8d0169f8"), "lod_ib": (None, "908c5aa3"), "lod_vb0": ("c1809c23", "c4f47348"), "index_count":300     , "lod_index_count":84   },
        ]
    },
    {
        "name": "Lifeng",
        "components": [
            { "index": 0, "ib": ("399f9090", "c39513f5"), "vb0": ("4e01d2f3", "4ac3d1a2"), "lod_ib": (None, "57473cb4"), "lod_vb0": ("d07403b8", "a3fb3c3d"), "index_count":110691  , "lod_index_count":49692 },
            { "index": 1, "ib": ("ce2104b9", "a7ebd04c"), "vb0": ("ee164e61", "6110f066"), "lod_ib": (None, "1ee62cae"), "lod_vb0": ("2c642d42", "41ec1fb2"), "index_count":47496   , "lod_index_count":23919 },
            { "index": 2, "ib": ("bacce5c3", "463965d1"), "vb0": ("7b193d67", "31bd8625"), "lod_ib": (None, "5f10d131"), "lod_vb0": ("f7d43f98", "9bf9f503"), "index_count":447     , "lod_index_count":327   },
            { "index": 3, "ib": ("028ca749", "721b3f91"), "vb0": ("e3bc8710", "91f4552d"), "lod_ib": (None, "4fdfe7cf"), "lod_vb0": ("83c608d6", "6e8e7f4c"), "index_count":7977    , "lod_index_count":4716  },
            { "index": 4, "ib": ("28eba972", "200a5e0c"), "vb0": ("451d6f92", "41a88e35"), "lod_ib": (None, "ca67ad77"), "lod_vb0": ("cfcd6a9a", "1a728145"), "index_count":12072   , "lod_index_count":12072 },
            { "index": 5, "ib": ("a22da71f", "07176c3a"), "vb0": ("62dc7c2f", "537d2d24"), "lod_ib": (None, "4d18faa4"), "lod_vb0": ("7326df8c", "71a4d328"), "index_count":1908    , "lod_index_count":1908  },
            { "index": 6, "ib": ("f5ebddc6", "475f38d4"), "vb0": ("04569828", "848e0ed6"), "lod_ib": (None, "dbd03de2"), "lod_vb0": ("0b3c92b8", "a166d552"), "index_count":768     , "lod_index_count":768   },
            { "index": 8, "ib": ("3edc2eab", "8100087b"), "vb0": ("0757cda9", "e601daaf"), "lod_ib": (None, "38d56a87"), "lod_vb0": ("256fa493", "442ab215"), "index_count":76335   , "lod_index_count":25266 },
            { "index": 9, "ib": ("18f7ec53", "82f3d9f3"), "vb0": ("fe9664c9", "f3670304"), "lod_ib": (None, "e88d7028"), "lod_vb0": ("193c157f", "830a907d"), "index_count":600     , "lod_index_count":216   },
        ]
    },
    {
        "name": "Catcher",
        "components": [
            { "index": 0 , "ib": ("ce502b85", "b0ff0909"), "vb0": ("2c78d727", "c771de85"), "lod_ib": (None, "b3fc7d59"), "lod_vb0": ("77fe8d97", "ad78f7c3"), "index_count":33957   , "lod_index_count":19734 },
            { "index": 1 , "ib": ("abc5f094", "e397f438"), "vb0": ("d9463006", "f6035922"), "lod_ib": (None, "18391bec"), "lod_vb0": ("592a38e0", "2b4011a8"), "index_count":9132    , "lod_index_count":5520  },
            { "index": 2 , "ib": ("80bbbc51", "84fda30d"), "vb0": ("d98a98ab", "01350d50"), "lod_ib": (None, "89a55e0f"), "lod_vb0": ("a4c53f2c", "68990c85"), "index_count":669     , "lod_index_count":396   },
            { "index": 3 , "ib": ("89947655", "3d8eaf7f"), "vb0": ("d4525dd2", "9795c104"), "lod_ib": (None, None)      , "lod_vb0": (None, None),             "index_count":9792    , "lod_index_count":None  },
            { "index": 4 , "ib": ("e1ac0d2e", "37d708a9"), "vb0": ("ada2b75e", "55dcc543"), "lod_ib": (None, "266b706b"), "lod_vb0": ("df909a5b", "ef44d99e"), "index_count":1650    , "lod_index_count":906   },
            { "index": 5 , "ib": ("bdec9197", "f4eb30e3"), "vb0": ("7866c67a", "a03d0365"), "lod_ib": (None, "d85c2dc8"), "lod_vb0": ("70b6e8d7", "7b8f13d1"), "index_count":822     , "lod_index_count":522   },
            { "index": 7 , "ib": ("6a5edb92", "48c9fdf7"), "vb0": ("6fdaf448", "11d0d8cb"), "lod_ib": (None, "d2a033d7"), "lod_vb0": ("cea9e251", "5cff83e7"), "index_count":13125   , "lod_index_count":11862 },
            { "index": 8 , "ib": ("6ae56a6f", "8680e912"), "vb0": ("3cf82098", "e4ffa43b"), "lod_ib": (None, "bc43852e"), "lod_vb0": ("90259a93", "32b58cc7"), "index_count":80046   , "lod_index_count":47640 },
            { "index": 9 , "ib": ("32389359", "7a23c2e9"), "vb0": ("db6cbf7a", "433ee63f"), "lod_ib": (None, "36f0e903"), "lod_vb0": ("82d00dc3", "27a452f6"), "index_count":35979   , "lod_index_count":22446 },
            { "index": 10, "ib": ("fb784a7c", "ccacd117"), "vb0": ("05a4ae6a", "72435fd8"), "lod_ib": (None, "14b31705"), "lod_vb0": ("a088f7c0", "99c821ba"), "index_count":204     , "lod_index_count":132   },
            { "index": 11, "ib": ("a18315cb", "65c4d414"), "vb0": ("13013649", "0c63ed2a"), "lod_ib": (None, "8c288bc1"), "lod_vb0": ("72f054e7", "d9ae0bc0"), "index_count":264     , "lod_index_count":150   },
        ]
    },
    {
        "name": "Tangtang",
        "components": [
            { "index": 0 , "ib": (None, "40e4dccb"), "vb0": (None, "1884ea87"), "lod_ib": (None, "7d77839f"), "lod_vb0": (None, "05bcba4d"), "index_count": 34899, "lod_index_count": 16173 },
            { "index": 1 , "ib": (None, "4f006df1"), "vb0": (None, "d843a707"), "lod_ib": (None, "25dc6ff6"), "lod_vb0": (None, "1e3b87d5"), "index_count": 3444,  "lod_index_count": 1308  },
            { "index": 2 , "ib": (None, "eddaabb8"), "vb0": (None, "f4c925ce"), "lod_ib": (None, "0e74012c"), "lod_vb0": (None, "b4192aa2"), "index_count": 110412,"lod_index_count": 48447 },
            { "index": 3 , "ib": (None, "d696bdf6"), "vb0": (None, "760090f4"), "lod_ib": (None, "53d9ced1"), "lod_vb0": (None, "dc4cb592"), "index_count": 11214, "lod_index_count": 11214 },
            { "index": 4 , "ib": (None, "7dfd4cd1"), "vb0": (None, "9a0f3018"), "lod_ib": (None, "f85a94c5"), "lod_vb0": (None, "541c883d"), "index_count": 303,   "lod_index_count": 147   },
            { "index": 5 , "ib": (None, "c1a5d542"), "vb0": (None, "7a3d1629"), "lod_ib": (None, None)      , "lod_vb0": (None, None),       "index_count": 585,   "lod_index_count": None  },
            { "index": 6 , "ib": (None, "b4266c30"), "vb0": (None, "876fe557"), "lod_ib": (None, None)      , "lod_vb0": (None, None),       "index_count": 102,   "lod_index_count": None  },
            { "index": 7 , "ib": (None, "a828d5fb"), "vb0": (None, "b9e1cf27"), "lod_ib": (None, "9509be12"), "lod_vb0": (None, "433064a6"), "index_count": 22587, "lod_index_count": 14973 },
            { "index": 8 , "ib": (None, "b5915079"), "vb0": (None, "97d6fcf9"), "lod_ib": (None, "a3272e57"), "lod_vb0": (None, "640b2815"), "index_count": 13728, "lod_index_count": 6483  },
            { "index": 9 , "ib": (None, "3f9d0528"), "vb0": (None, "f7dfa7e7"), "lod_ib": (None, "eb319e54"), "lod_vb0": (None, "0e2d64a6"), "index_count": 9504,  "lod_index_count": 5565  },
            { "index": 10, "ib": (None, "8a76f261"), "vb0": (None, "b0800d8a"), "lod_ib": (None, "7a5ccaa0"), "lod_vb0": (None, "3b2bf59e"), "index_count": 27039, "lod_index_count": 12267 },
        ]
    },
    {
        "name": "Da Pan",
        "components": [
            { "index": 0, "ib": (None, "b4e10c34"), "vb0": (None, "5a440c44"), "lod_ib": (None, "8878c5a4"), "lod_vb0": (None, "823b2daf"), "index_count":255132  , "lod_index_count":6726 },
            { "index": 1, "ib": (None, "0423f8d0"), "vb0": (None, "bd404ad8"), "lod_ib": (None, None)      , "lod_vb0": (None, None),       "index_count":384     , "lod_index_count":None },
            { "index": 2, "ib": (None, "f6df08dd"), "vb0": (None, "40a53558"), "lod_ib": (None, None)      , "lod_vb0": (None, None),       "index_count":2454    , "lod_index_count":None },
            { "index": 3, "ib": (None, "6e9617ad"), "vb0": (None, "0b5eb492"), "lod_ib": (None, "081c9151"), "lod_vb0": (None, "b3c059fb"), "index_count":78624   , "lod_index_count":19941},
            { "index": 4, "ib": (None, "131ef5b2"), "vb0": (None, "5ba1b4ce"), "lod_ib": (None, "131ef5b2"), "lod_vb0": (None, "b1314f51"), "index_count":1452    , "lod_index_count":1452 },
            { "index": 5, "ib": (None, "7a81aaa6"), "vb0": (None, "523ee9f8"), "lod_ib": (None, None)      , "lod_vb0": (None, None),       "index_count":29334   , "lod_index_count":None },
            { "index": 6, "ib": (None, "14486ed3"), "vb0": (None, "db556161"), "lod_ib": (None, "de5ca71d"), "lod_vb0": (None, "f9c0edb1"), "index_count":4866    , "lod_index_count":1176 },
            { "index": 7, "ib": (None, "8601be54"), "vb0": (None, "677259c4"), "lod_ib": (None, "290d46ac"), "lod_vb0": (None, "75a18663"), "index_count":33858   , "lod_index_count":15309},
        ]
    }
]


SUBSTITUTIONS: list[tuple[str, str]] = [
    ("ib", "ib"),
    ("vb0", "ib"),
    ("lod_ib", "lod_ib"),
    ("lod_vb0", "lod_ib"),
]


_HASH_RE = re.compile(r"^\s*hash\s*=\s*([0-9a-fA-F]+)", re.IGNORECASE)
_MIC_RE = re.compile(r"^\s*match_index_count\s*=", re.IGNORECASE)
_SECTION_RE = re.compile(r"^\s*\[(.+)\]\s*$")
_RUN_CMD_RE = re.compile(r"^\s*run\s*=\s*(CommandList_Draw_\S+)", re.IGNORECASE)
_OBJ_DET_RE = re.compile(r"^\s*\$object_detected\s*=\s*1", re.IGNORECASE)
_LOD_DET_RE = re.compile(r"^\s*\$lod_detected\s*=\s*0", re.IGNORECASE)
_TO_RE = re.compile(r"^TextureOverride_Component(\d+)$", re.IGNORECASE)
_TO_LOD_RE = re.compile(r"^TextureOverride_Component(\d+)_LOD\d*$", re.IGNORECASE)


@dataclass
class HashMapping:
    _map: dict[str, str] = field(default_factory=dict, repr=False)
    _labels: dict[str, str] = field(default_factory=dict, repr=False)
    _index_counts: dict[str, tuple[int, str, bool]] = field(default_factory=dict, repr=False)

    @staticmethod
    def from_characters(characters: list[dict[str, Any]]) -> "HashMapping":
        hm = HashMapping()
        for char in characters:
            name = char["name"]
            for comp in char["components"]:
                idx = comp["index"]
                ib_new = (comp.get("ib") or (None, None))[1]
                lod_new = (comp.get("lod_ib") or (None, None))[1]
                skip_lod = bool(ib_new and lod_new and ib_new.lower() == lod_new.lower())

                for old_field, new_field in SUBSTITUTIONS:
                    if skip_lod and old_field in ("lod_ib", "lod_vb0"):
                        continue
                    old_pair = comp.get(old_field)
                    new_pair = comp.get(new_field)
                    if not old_pair or not new_pair:
                        continue
                    old_hash = old_pair[0].strip() if old_pair[0] else old_pair[0]
                    new_hash = new_pair[1].strip() if new_pair[1] else new_pair[1]
                    if not old_hash or not new_hash or old_hash == new_hash:
                        continue
                    label = f"{old_field.upper()} -> {new_field.upper()}"
                    hm._map[old_hash.lower()] = new_hash.lower()
                    hm._labels[old_hash.lower()] = f"{name} | Comp {idx} | {label}"

                prefix = f"{name} | Comp {idx}"
                if ib_new and comp.get("index_count") is not None:
                    hm._index_counts[ib_new.lower()] = (comp["index_count"], prefix, False)
                if lod_new and not skip_lod and comp.get("lod_index_count") is not None:
                    hm._index_counts[lod_new.lower()] = (comp["lod_index_count"], prefix, True)

            for old_hash, new_hash in char.get("textures", []):
                if old_hash and new_hash and old_hash != new_hash:
                    hm._map[old_hash.lower()] = new_hash.lower()
                    hm._labels[old_hash.lower()] = f"{name} | Texture {old_hash.lower()} | Texture"
        return hm

    def pattern(self) -> re.Pattern[str]:
        if not self._map:
            raise ValueError("HashMapping has no entries; nothing to substitute.")
        return re.compile("|".join(re.escape(k) for k in self._map), flags=re.IGNORECASE)

    def get(self, old: str) -> tuple[str, str] | None:
        key = old.lower()
        if key in self._map:
            return self._map[key], self._labels[key]
        return None

    def get_index_count(self, hash_val: str) -> tuple[int, str, bool] | None:
        return self._index_counts.get(hash_val.lower())


@dataclass
class IniHit:
    label: str
    old: str
    new: str


@dataclass
class IniLine:
    original: str

    @property
    def is_hash_line(self) -> bool:
        return self.original.lstrip().lower().startswith("hash")

    @property
    def is_section_header(self) -> bool:
        stripped = self.original.strip()
        return stripped.startswith("[") and stripped.endswith("]")

    @property
    def header_name(self) -> str:
        return self.original.strip()[1:-1] if self.is_section_header else ""

    def replace(self, pattern: re.Pattern[str], mapping: HashMapping) -> tuple[str, list[IniHit]]:
        if not self.is_hash_line:
            return self.original, []

        match = _HASH_RE.match(self.original)
        if not match:
            return self.original, []

        old_hash = match.group(1)
        result = mapping.get(old_hash)
        if not result:
            return self.original, []

        new_hash, label = result
        new_line = self.original[:match.start(1)] + new_hash + self.original[match.end(1):]
        return new_line, [IniHit(label=label, old=old_hash.lower(), new=new_hash)]


@dataclass
class SpecialCase:
    name: str
    trigger_hash: str
    new_hash: str
    index_count: int
    suffix: str


SPECIAL_CASES = [
    SpecialCase("Ardelia", "cc35f7fa", "79054f88", 48735, "_Patched"),
    SpecialCase("Akekuri", "a536a1d4", "3852bca5", 54378, "_Patched"),
    SpecialCase("Akekuri_LOD", "e3eb0556", "635017df", 12390, "_Patched_LoD"),
    SpecialCase("Ardelia_LOD", "7e4ccfbf", "cc4bfc2e", 7182, "_Patched"),
    SpecialCase("Alesh", "6985f42b", "6fb8a949", 20520, "_Patched"),
    SpecialCase("Alesh_LOD", "6985f42b", "8d591a7a", 7560, "_Patched_LoD"),
    SpecialCase("Tangtang", "4f006df1", "ef7a4f55", 65436, "_Patched"),
    SpecialCase("Tangtang_LOD", "25dc6ff6", "ac4ba24b", 9156, "_Patched_LoD"),
    SpecialCase("Estella", "fa0d4a01", "0d744abd", 28500, "_Patched"),
    SpecialCase("Estella_LOD", "4293dd55", "022ce373", 7665, "_Patched_LoD"),
]


OLD_SHADER_BLOCK = """\
[ShaderOverridevs22]
hash = 617db42150841836
filter_index = 200

[ShaderOverridevs2]
hash = 847947b4a1ad40cf
filter_index = 200

[ShaderOverridevs10]
hash = cada6d476255bdcf
filter_index = 201

[ShaderOverridevs1]
hash = d9d6448a7b62687e
filter_index = 202

[ShaderOverridevs33]
hash = e8d242aae0b3bacf
filter_index = 203

[ShaderOverridevs88]
hash = f0e7d4b491273aae
filter_index = 203"""

NEW_SHADER_BLOCK = """\
[ShaderOverridevs1000]
hash = 241383a9d64b4978
filter_index = 200
allow_duplicate_hash = overrule

[ShaderOverridevs1001]
hash = 6733250da4e23fd6
filter_index = 200
allow_duplicate_hash = overrule

[ShaderOverridevs1002]
hash = 9bac7486f7930a24
filter_index = 201
allow_duplicate_hash = overrule

[ShaderOverridevs1003]
hash = b30cc5ad521e0700
filter_index = 202
allow_duplicate_hash = overrule

[ShaderOverridevs1004]
hash = 4921f64a7c74226d
filter_index = 203
allow_duplicate_hash = overrule

[ShaderOverridevs1005]
hash = 1b835d0e8dbbfb8f
filter_index = 203
allow_duplicate_hash = overrule

[ShaderOverridevs1006]
hash = 06c94dd56f447210
filter_index = 204
allow_duplicate_hash = overrule

[ShaderOverridevs1007]
hash = f47b1f797f5831d0
filter_index = 204
allow_duplicate_hash = overrule"""

OLD_SHADER_HASHES = {
    "617db42150841836",
    "847947b4a1ad40cf",
    "cada6d476255bdcf",
    "d9d6448a7b62687e",
    "e8d242aae0b3bacf",
    "f0e7d4b491273aae",
}

NEW_SHADER_HASHES = {
    "241383a9d64b4978",
    "6733250da4e23fd6",
    "9bac7486f7930a24",
    "b30cc5ad521e0700",
    "4921f64a7c74226d",
    "1b835d0e8dbbfb8f",
    "06c94dd56f447210",
    "f47b1f797f5831d0",
}

END_FIELD_FIXED_MARKER = "; endfield_mod_fix: v1.2 applied"
LEGACY_PS_T_SHIFT_MARKER = ";ps-t-shifted"
END_FIELD_FIXED_MARKER_RE = re.compile(r"^\s*;\s*endfield_mod_fix:\s*v1\.2\s+applied\s*$", re.IGNORECASE)
LEGACY_PS_T_SHIFT_MARKER_RE = re.compile(r"^\s*;\s*ps-t-shifted\s*$", re.IGNORECASE)
END_FIELD_13_OLD_HASH = "b30cc5ad521e0700"
END_FIELD_13_NEW_HASH = "1eaaa259e9a4285b"
END_FIELD_13_SECTION_SUFFIX = "_13"
END_FIELD_13_FILTER_INDEX = 202
END_FIELD_13_DUPLICATE_POLICY = "overrule"

START_INDEX = 1000
SECTION_PREFIX = "ShaderOverridevs"
SUPPORTED_FILTERS = tuple(range(200, 205))
HASH_RULES: dict[int, list[str]] = {
    200: ["241383a9d64b4978", "6733250da4e23fd6"],
    201: ["9bac7486f7930a24"],
    202: ["b30cc5ad521e0700"],
    203: ["4921f64a7c74226d", "1b835d0e8dbbfb8f"],
    204: ["06c94dd56f447210", "f47b1f797f5831d0"],
}

SECTION_HEADER_RE = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")
FILTER_INDEX_RE = re.compile(r"^\s*filter_index\s*=\s*(\d+)\s*(?:[;#].*)?$", re.IGNORECASE)
ALLOW_DUPLICATE_HASH_RE = re.compile(r"^\s*allow_duplicate_hash\s*=\s*(\S+)\s*(?:[;#].*)?$", re.IGNORECASE)
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


@dataclass(frozen=True)
class IniSection:
    name: str
    start: int
    end: int
    lines: list[str]


@dataclass
class StageResult:
    name: str
    changed: bool
    details: list[str] = field(default_factory=list)
    hits: list[IniHit] = field(default_factory=list)


@dataclass
class FilePlan:
    path: Path
    relpath: str
    original_text: str
    new_text: str
    encoding: str
    stages: list[StageResult]

    @property
    def changed(self) -> bool:
        return self.new_text != self.original_text


@dataclass(frozen=True)
class RunOptions:
    root: Path
    dry_run: bool = False
    include_disabled: bool = False
    force_new_version: bool = False
    enable_fixmenu: bool = False


@dataclass
class FixPlan:
    root: Path
    hotfix_root: Path
    file_plans: list[FilePlan]
    hotfix_files: list[Path]
    skipped_new_version: int


def detect_encoding(data: bytes) -> str:
    if data.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        return "utf-16"
    for encoding in ("utf-8", "gb18030"):
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def load_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    encoding = detect_encoding(data)
    return data.decode(encoding), encoding


def detect_newline(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\n" in text:
        return "\n"
    if "\r" in text:
        return "\r"
    return "\n"


def join_split_lines(lines: list[str], newline: str, had_final_newline: bool) -> str:
    text = newline.join(lines)
    if had_final_newline and text:
        text += newline
    return text


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def restore_newlines(text: str, newline: str) -> str:
    return text.replace("\n", newline) if newline != "\n" else text


def apply_special_cases(lines: list[str], special_cases: list[SpecialCase], newline: str) -> tuple[list[str], list[IniHit]]:
    out_lines: list[str] = []
    hits: list[IniHit] = []
    sections: list[list[str]] = []
    current_section: list[str] = []

    for line in lines:
        if line.strip().startswith("[") and line.strip().endswith("]"):
            if current_section:
                sections.append(current_section)
            current_section = [line]
        else:
            current_section.append(line)
    if current_section:
        sections.append(current_section)

    pending_inserts: list[tuple[int, list[str]]] = []

    for case in special_cases:
        new_hash_sections: list[int] = []
        trigger_sections: list[int] = []

        for idx, sec in enumerate(sections):
            for line in sec:
                m = _HASH_RE.match(line)
                if not m:
                    continue
                h = m.group(1).lower()
                if h == case.new_hash.lower():
                    new_hash_sections.append(idx)
                elif h == case.trigger_hash.lower():
                    trigger_sections.append(idx)

        if new_hash_sections:
            for sec_idx in new_hash_sections:
                sec = sections[sec_idx]
                has_mic = any(_MIC_RE.match(l) for l in sec)
                if has_mic:
                    continue
                for line_idx, line in enumerate(sec):
                    m = _HASH_RE.match(line)
                    if m and m.group(1).lower() == case.new_hash.lower():
                        sec.insert(line_idx + 1, f"match_index_count = {case.index_count}{newline}")
                        hits.append(IniHit(f"SPECIAL_CASE | {case.name}", case.new_hash, f"+ match_index_count {case.index_count}"))
                        break
        elif trigger_sections:
            for sec_idx in trigger_sections:
                sec = sections[sec_idx]
                new_sec: list[str] = []
                for idx, line in enumerate(sec):
                    if idx == 0 and line.strip().startswith("[") and line.strip().endswith("]"):
                        stripped = line.strip()
                        new_sec.append(f"{newline}{stripped[:-1]}{case.suffix}]{newline}")
                        continue

                    m = _HASH_RE.match(line)
                    if m and m.group(1).lower() == case.trigger_hash.lower():
                        new_sec.append(line[:m.start(1)] + case.new_hash + line[m.end(1):])
                        if not any(_MIC_RE.match(l) for l in sec):
                            new_sec.append(f"match_index_count = {case.index_count}{newline}")
                    elif _MIC_RE.match(line):
                        new_sec.append(re.sub(r"=\s*\d+", f"= {case.index_count}", line))
                    else:
                        new_sec.append(line)

                pending_inserts.append((sec_idx, new_sec))
                hits.append(IniHit(f"SPECIAL_CASE | {case.name}", case.trigger_hash, f"Duplicated -> {case.new_hash}"))

    for sec_idx, new_sec in sorted(pending_inserts, reverse=True):
        sections.insert(sec_idx + 1, new_sec)

    for sec in sections:
        out_lines.extend(sec)
    return out_lines, hits


def apply_efmi_hash_stage(content: str, mapping: HashMapping, pattern: re.Pattern[str], newline: str) -> tuple[str, StageResult]:
    original = content
    lines = [IniLine(line) for line in content.splitlines(keepends=True)]
    all_hits: list[IniHit] = []
    new_lines: list[str] = []
    skip_section = False

    for line in lines:
        if line.is_section_header:
            skip_section = "VertexLimitRaise" in line.header_name

        if skip_section:
            new_lines.append(line.original)
            continue

        new_line, hits = line.replace(pattern, mapping)
        new_lines.append(new_line)
        all_hits.extend(hits)

    final_lines: list[str] = []
    i = 0
    while i < len(new_lines):
        line_text = new_lines[i]
        final_lines.append(line_text)
        m = _HASH_RE.match(line_text)
        if m:
            hash_val = m.group(1).lower()
            idx_info = mapping.get_index_count(hash_val)
            if idx_info is not None:
                idx_count, prefix, is_lod = idx_info
                next_idx = i + 1
                already_has_mic = False
                while next_idx < len(new_lines):
                    ahead = new_lines[next_idx].strip()
                    if ahead.startswith("["):
                        break
                    if _MIC_RE.match(new_lines[next_idx]):
                        already_has_mic = True
                        break
                    next_idx += 1

                if not already_has_mic:
                    final_lines.append(f"match_index_count = {idx_count}{newline}")
                    label_type = "LOD_INDEX_COUNT" if is_lod else "INDEX_COUNT"
                    all_hits.append(IniHit(f"{prefix} | {label_type}", "None", str(idx_count)))
        i += 1

    sec_map: dict[str, dict[str, Any]] = {}
    cur_name: str | None = None
    for global_idx, line_text in enumerate(final_lines):
        sm = _SECTION_RE.match(line_text)
        if sm:
            cur_name = sm.group(1)
            sec_map[cur_name] = {"lines": [], "run_cmd": None}
        if cur_name is not None:
            sec_map[cur_name]["lines"].append((global_idx, line_text))
            rm = _RUN_CMD_RE.match(line_text)
            if rm:
                sec_map[cur_name]["run_cmd"] = rm.group(1).strip()

    lod_components: dict[str, str] = {}
    for sec_name, info in sec_map.items():
        m_lod = _TO_LOD_RE.match(sec_name)
        if m_lod and info["run_cmd"]:
            lod_components[m_lod.group(1)] = info["run_cmd"]

    insert_offsets: list[tuple[int, str]] = []
    for sec_name, info in sec_map.items():
        m_ib = _TO_RE.match(sec_name)
        if not m_ib:
            continue
        comp_num = m_ib.group(1)
        if comp_num not in lod_components:
            continue
        if info["run_cmd"] and info["run_cmd"] != lod_components[comp_num]:
            continue
        if any(_LOD_DET_RE.match(line_text) for _, line_text in info["lines"]):
            continue
        for global_idx, line_text in info["lines"]:
            if _OBJ_DET_RE.match(line_text):
                insert_offsets.append((global_idx, sec_name))
                break

    for global_idx, sec_name in sorted(insert_offsets, reverse=True):
        final_lines.insert(global_idx + 1, f"$lod_detected = 0{newline}")
        all_hits.append(IniHit(f"{sec_name} | LOD_DETECTED", "None", "$lod_detected = 0"))

    final_lines, special_hits = apply_special_cases(final_lines, SPECIAL_CASES, newline)
    all_hits.extend(special_hits)

    new_content = "".join(final_lines)
    details: list[str] = []
    if all_hits:
        hash_hits = sum(1 for hit in all_hits if hit.old != "None" and not hit.new.startswith("+ match_index_count"))
        index_hits = sum(1 for hit in all_hits if "INDEX_COUNT" in hit.label or hit.new.startswith("+ match_index_count"))
        lod_hits = sum(1 for hit in all_hits if "LOD_DETECTED" in hit.label)
        special_hits_count = sum(1 for hit in all_hits if hit.label.startswith("SPECIAL_CASE"))
        details.append(f"hash/index migration hits: {len(all_hits)}")
        if hash_hits:
            details.append(f"hash replacements or duplications: {hash_hits}")
        if index_hits:
            details.append(f"match_index_count insertions/updates: {index_hits}")
        if lod_hits:
            details.append(f"$lod_detected insertions: {lod_hits}")
        if special_hits_count:
            details.append(f"special case hits: {special_hits_count}")

    return new_content, StageResult("EFMI_Fix_F", new_content != original, details, all_hits)


def has_cross_ib(content: str) -> bool:
    return bool(re.search(r"CustomShader_ExtractCB1|cross\s*[-_ ]?\s*ib", content, flags=re.IGNORECASE))


def has_conditional_texture_bindings(content: str) -> bool:
    depth = 0
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue

        keyword = stripped.split(None, 1)[0].lower()
        if keyword == "endif":
            depth = max(0, depth - 1)

        m = re.match(r"ps-t(\d+)\s*=\s*(\S+)", stripped, flags=re.IGNORECASE)
        if m and depth > 0 and int(m.group(1)) >= 2:
            res = m.group(2).lower()
            if any(k in res for k in ("diffusemap", "lightmap", "normalmap")):
                return True

        if keyword == "if":
            depth += 1

    return False


def needs_endfield_fix1(content: str) -> bool:
    return any(h in content for h in OLD_SHADER_HASHES)


def already_endfield_fix1(content: str) -> bool:
    return any(h in content for h in NEW_SHADER_HASHES)


def needs_endfield_fix2(content: str) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(";") or "CheckTextureOverride" in stripped:
            continue
        m = re.match(r"ps-t(\d+)\s*=\s*(\S+)", stripped)
        if m and int(m.group(1)) >= 2:
            res = m.group(2).lower()
            if any(k in res for k in ("diffusemap", "lightmap", "normalmap")):
                return True
    return False


def apply_endfield_fix1(content: str, newline: str) -> tuple[str, bool]:
    normalized = normalize_newlines(content)
    changed = False
    if OLD_SHADER_BLOCK in normalized:
        return restore_newlines(normalized.replace(OLD_SHADER_BLOCK, NEW_SHADER_BLOCK), newline), True

    old_sections = [
        ("[ShaderOverridevs22]", "617db42150841836"),
        ("[ShaderOverridevs2]", "847947b4a1ad40cf"),
        ("[ShaderOverridevs10]", "cada6d476255bdcf"),
        ("[ShaderOverridevs1]", "d9d6448a7b62687e"),
        ("[ShaderOverridevs33]", "e8d242aae0b3bacf"),
        ("[ShaderOverridevs88]", "f0e7d4b491273aae"),
    ]
    for section, hash_val in old_sections:
        pattern = re.compile(
            re.escape(section) + r"\s*\nhash\s*=\s*" + re.escape(hash_val) + r".*?(?=\n\[|\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        if pattern.search(normalized):
            normalized = pattern.sub("", normalized)
            changed = True

    if changed:
        insert_after = re.search(
            r"(\[CustomShader_RedirectCB1\].*?ResourceFakeCB1\s*=\s*copy\s*ResourceFakeCB1_UAV)",
            normalized,
            re.DOTALL | re.IGNORECASE,
        )
        if insert_after:
            pos = insert_after.end()
            normalized = normalized[:pos] + "\n\n" + NEW_SHADER_BLOCK + normalized[pos:]
        else:
            normalized = NEW_SHADER_BLOCK + "\n\n" + normalized

    return restore_newlines(normalized, newline), changed


def apply_endfield_fix2_shift(content: str, newline: str) -> tuple[str, bool]:
    lines = content.splitlines()
    had_final_newline = content.endswith(("\n", "\r"))
    result: list[str] = []
    changed = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(";") or "CheckTextureOverride" in line:
            result.append(line)
            continue
        m = re.match(r"^(\s*ps-t)(\d+)(\s*=\s*)(\S+.*)$", line)
        if m and int(m.group(2)) >= 2:
            res = m.group(4).lower()
            if any(k in res for k in ("diffusemap", "lightmap", "normalmap")):
                result.append(m.group(1) + str(int(m.group(2)) + 2) + m.group(3) + m.group(4))
                changed = True
                continue
        result.append(line)

    return join_split_lines(result, newline, had_final_newline), changed


def section_has_conditional_texture_bindings(lines: list[str]) -> bool:
    depth = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue

        keyword = stripped.split(None, 1)[0].lower()
        if keyword == "endif":
            depth = max(0, depth - 1)

        m = re.match(r"ps-t(\d+)\s*=\s*(\S+)", stripped, flags=re.IGNORECASE)
        if m and depth > 0 and int(m.group(1)) >= 2:
            res = m.group(2).lower()
            if any(k in res for k in ("diffusemap", "lightmap", "normalmap")):
                return True

        if keyword == "if":
            depth += 1

    return False


def shift_ps_t_line(line: str, offset: int = 2) -> tuple[str, bool]:
    stripped = line.strip()
    if stripped.startswith(";") or "CheckTextureOverride" in line:
        return line, False

    m = re.match(r"^(\s*ps-t)(\d+)(\s*=\s*)(\S+.*)$", line, flags=re.IGNORECASE)
    if not m or int(m.group(2)) < 2:
        return line, False

    res = m.group(4).lower()
    if not any(k in res for k in ("diffusemap", "lightmap", "normalmap")):
        return line, False

    return m.group(1) + str(int(m.group(2)) + offset) + m.group(3) + m.group(4), True


def apply_endfield_fix2_conditional_shift(content: str, newline: str) -> tuple[str, bool, int]:
    lines = content.splitlines(keepends=True)
    sections = collect_sections(lines)
    changed = False
    changed_sections = 0

    for section in sections:
        raw_section_lines = [line.rstrip("\r\n") for line in section.lines]
        if not section_has_conditional_texture_bindings(raw_section_lines):
            continue

        section_changed = False
        for line_index in range(section.start, section.end):
            raw_line = lines[line_index]
            line_body = raw_line.rstrip("\r\n")
            line_end = raw_line[len(line_body):]
            new_body, line_changed = shift_ps_t_line(line_body)
            if line_changed:
                lines[line_index] = new_body + line_end
                changed = True
                section_changed = True

        if section_changed:
            changed_sections += 1

    return "".join(lines), changed, changed_sections


def shift_nonconditional_light_normal_lines(lines: list[str], sections: list[IniSection]) -> int:
    changed = 0

    for section in sections:
        raw_section_lines = [line.rstrip("\r\n") for line in section.lines]
        if section_has_conditional_texture_bindings(raw_section_lines):
            continue

        slot_resources: dict[int, str] = {}
        for raw_line in section.lines:
            stripped = raw_line.strip()
            if stripped.startswith(";"):
                continue
            m_slot = re.match(r"ps-t(\d+)\s*=\s*(\S+)", stripped, flags=re.IGNORECASE)
            if m_slot:
                slot_resources[int(m_slot.group(1))] = m_slot.group(2).lower()

        original_light_slots = {
            slot for slot, resource in slot_resources.items()
            if "lightmap" in resource and slot in {14, 15}
        }
        has_shifted_light = any("lightmap" in resource and slot in {16, 17} for slot, resource in slot_resources.items())
        has_shifted_normal = any("normalmap" in resource and slot in {17, 18} for slot, resource in slot_resources.items())

        for line_index in range(section.start, section.end):
            raw_line = lines[line_index]
            line_body = raw_line.rstrip("\r\n")
            line_end = raw_line[len(line_body):]
            m = re.match(r"^(\s*ps-t)(\d+)(\s*=\s*)(\S+.*)$", line_body, flags=re.IGNORECASE)
            if not m:
                continue

            slot = int(m.group(2))
            resource = m.group(4).lower()
            new_slot: int | None = None

            if "lightmap" in resource and slot in {14, 15} and not has_shifted_light:
                new_slot = slot + 2
            elif "normalmap" in resource:
                if slot in {14, 15} and not has_shifted_normal:
                    new_slot = slot + 2
                elif slot == 16 and original_light_slots and not has_shifted_normal:
                    new_slot = 18

            if new_slot is None:
                continue

            lines[line_index] = f"{m.group(1)}{new_slot}{m.group(3)}{m.group(4)}{line_end}"
            changed += 1

    return changed


def apply_endfield_fix2_rabbitfx(content: str, newline: str) -> tuple[str, bool]:
    lines = content.splitlines()
    had_final_newline = content.endswith(("\n", "\r"))
    result: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith(";") or "CheckTextureOverride" in line:
            result.append(line)
            i += 1
            continue

        m = re.match(r"^(\s*)ps-t(\d+)\s*=\s*(\S+)", line)
        if m and int(m.group(2)) >= 2:
            indent = m.group(1)
            group: list[tuple[int, str, str]] = []
            j = i
            while j < len(lines):
                lj = lines[j]
                mj = re.match(r"^\s*ps-t(\d+)\s*=\s*(\S+)", lj)
                if mj and int(mj.group(1)) >= 2 and "CheckTextureOverride" not in lj and not lj.strip().startswith(";"):
                    group.append((int(mj.group(1)), mj.group(2), lj))
                    j += 1
                else:
                    break

            if group:
                diffuse = lightmap = normalmap = None
                for _, res, _ in group:
                    rl = res.lower()
                    if "diffuse" in rl:
                        diffuse = res
                    elif "light" in rl or "lightmap" in rl:
                        lightmap = res
                    elif "normal" in rl or "normalmap" in rl:
                        normalmap = res

                if diffuse:
                    result.append(f"{indent}Resource\\RabbitFX\\Diffuse = ref {diffuse}")
                    if lightmap:
                        result.append(f"{indent}Resource\\RabbitFX\\Lightmap = ref {lightmap}")
                    if normalmap:
                        result.append(f"{indent}Resource\\RabbitFX\\Normalmap = ref {normalmap}")
                    result.append(f"{indent}run = CommandList\\RabbitFX\\SetTextures")
                    changed = True
                    i = j
                    continue

                for _, _, orig in group:
                    mm = re.match(r"^(\s*ps-t)(\d+)(\s*=\s*.+)$", orig)
                    if mm and int(mm.group(2)) >= 2:
                        result.append(mm.group(1) + str(int(mm.group(2)) + 2) + mm.group(3))
                        changed = True
                    else:
                        result.append(orig)
                i = j
                continue

        result.append(line)
        i += 1

    return join_split_lines(result, newline, had_final_newline), changed


def apply_endfield_stage(content: str, newline: str) -> tuple[str, StageResult]:
    original = content
    details: list[str] = []

    if needs_endfield_fix1(content) and not already_endfield_fix1(content):
        content, changed = apply_endfield_fix1(content, newline)
        if changed:
            details.append("ShaderOverride VS hashes updated")

    if needs_endfield_fix2(content):
        if has_cross_ib(content):
            content, changed = apply_endfield_fix2_shift(content, newline)
            if changed:
                details.append("PS-T slots shifted +2 (cross-IB detected)")
        elif has_conditional_texture_bindings(content):
            content, changed, changed_sections = apply_endfield_fix2_conditional_shift(content, newline)
            if changed:
                details.append(f"PS-T slots shifted +2 in {changed_sections} conditional texture section(s)")
        else:
            content, changed = apply_endfield_fix2_rabbitfx(content, newline)
            if changed:
                details.append("PS-T slots replaced with RabbitFX (no cross-IB)")

    return content, StageResult("endfield_mod_fix", content != original, details)


def collect_sections(lines: list[str]) -> list[IniSection]:
    headers: list[tuple[int, str]] = []
    for index, raw_line in enumerate(lines):
        match = SECTION_HEADER_RE.match(raw_line.rstrip("\r\n"))
        if match:
            headers.append((index, match.group("name").strip()))

    sections: list[IniSection] = []
    for section_index, (start, name) in enumerate(headers):
        end = headers[section_index + 1][0] if section_index + 1 < len(headers) else len(lines)
        sections.append(IniSection(name=name, start=start, end=end, lines=lines[start:end]))
    return sections


def extract_filter_index(section: IniSection) -> int | None:
    for raw_line in section.lines:
        match = FILTER_INDEX_RE.match(raw_line.rstrip("\r\n"))
        if match:
            return int(match.group(1))
    return None


def is_ps_target_section(section: IniSection) -> bool:
    target_section_re = re.compile(rf"^{re.escape(SECTION_PREFIX)}\d+$", re.IGNORECASE)
    if not target_section_re.match(section.name):
        return False
    return extract_filter_index(section) in SUPPORTED_FILTERS


def build_ps_replacement_lines(newline: str) -> tuple[list[str], int]:
    generated: list[str] = []
    next_index = START_INDEX
    added = 0

    for filter_index in SUPPORTED_FILTERS:
        cleaned: list[str] = []
        for raw_hash in HASH_RULES.get(filter_index, []):
            hash_value = str(raw_hash).strip()
            if not hash_value:
                continue
            if not HEX_RE.fullmatch(hash_value):
                raise ValueError(f"Invalid hash {raw_hash!r} in HASH_RULES[{filter_index}].")
            cleaned.append(hash_value.lower())

        for hash_value in cleaned:
            generated.extend([
                f"[{SECTION_PREFIX}{next_index}]{newline}",
                f"hash = {hash_value}{newline}",
                f"filter_index = {filter_index}{newline}",
                f"allow_duplicate_hash = overrule{newline}",
                newline,
            ])
            next_index += 1
            added += 1

    if generated:
        generated.pop()
    return generated, added


def merge_ps_lines(original_lines: list[str], target_sections: list[IniSection], replacement_lines: list[str]) -> list[str]:
    result: list[str] = []
    cursor = 0
    inserted = False

    for section in target_sections:
        result.extend(original_lines[cursor:section.start])
        if not inserted:
            result.extend(replacement_lines)
            inserted = True
        cursor = section.end

    result.extend(original_lines[cursor:])
    return result


def apply_ps_t_shift_stage(content: str, newline: str) -> tuple[str, StageResult]:
    original = content
    lines = content.splitlines(keepends=True)
    sections = collect_sections(lines)
    target_sections = [section for section in sections if is_ps_target_section(section)]

    if not target_sections:
        return content, StageResult("ps_t_shift", False, [])

    replacement_lines, added = build_ps_replacement_lines(newline)
    new_lines = merge_ps_lines(lines, target_sections, replacement_lines)
    new_content = "".join(new_lines)
    details = [f"removed {len(target_sections)} ShaderOverridevs section(s), generated {added} section(s)"]
    return new_content, StageResult("ps_t_shift", new_content != original, details)


def section_name_equals(section: IniSection, name: str) -> bool:
    return section.name.strip().casefold() == name.casefold()


def find_ini_section(sections: list[IniSection], name: str) -> IniSection | None:
    for section in sections:
        if section_name_equals(section, name):
            return section
    return None


def section_has_hash_value(section: IniSection, hash_value: str) -> bool:
    target = hash_value.lower()
    for raw_line in section.lines:
        match = _HASH_RE.match(raw_line.rstrip("\r\n"))
        if match and match.group(1).lower() == target:
            return True
    return False


def section_has_duplicate_overrule(section: IniSection) -> bool:
    for raw_line in section.lines:
        match = ALLOW_DUPLICATE_HASH_RE.match(raw_line.rstrip("\r\n"))
        if match and match.group(1).casefold() == END_FIELD_13_DUPLICATE_POLICY:
            return True
    return False


def section_has_endfield_13_payload(section: IniSection) -> bool:
    return (
        section_has_hash_value(section, END_FIELD_13_NEW_HASH)
        and extract_filter_index(section) == END_FIELD_13_FILTER_INDEX
        and section_has_duplicate_overrule(section)
    )


def section_has_endfield_13_target_payload(section: IniSection) -> bool:
    return (
        section_has_hash_value(section, END_FIELD_13_OLD_HASH)
        and extract_filter_index(section) == END_FIELD_13_FILTER_INDEX
        and section_has_duplicate_overrule(section)
    )


def endfield_13_patch_section_name(section: IniSection) -> str:
    return f"{section.name}{END_FIELD_13_SECTION_SUFFIX}"


def find_endfield_13_target_sections(sections: list[IniSection]) -> list[IniSection]:
    return [
        section
        for section in sections
        if section_has_endfield_13_target_payload(section)
    ]


def endfield_13_patch_base_name(section: IniSection) -> str | None:
    suffix = END_FIELD_13_SECTION_SUFFIX.casefold()
    name = section.name.strip()
    if not name.casefold().endswith(suffix):
        return None
    return name[:-len(END_FIELD_13_SECTION_SUFFIX)]


def section_has_endfield_13_any_payload(section: IniSection) -> bool:
    return (
        (section_has_hash_value(section, END_FIELD_13_OLD_HASH) or section_has_hash_value(section, END_FIELD_13_NEW_HASH))
        and extract_filter_index(section) == END_FIELD_13_FILTER_INDEX
        and section_has_duplicate_overrule(section)
    )


def is_endfield_13_patch_section(section: IniSection, sections: list[IniSection]) -> bool:
    if not section_has_endfield_13_payload(section):
        return False

    base_name = endfield_13_patch_base_name(section)
    if not base_name:
        return False

    base_section = find_ini_section(sections, base_name)
    return base_section is not None and section_has_endfield_13_any_payload(base_section)


def find_endfield_13_restore_sections(sections: list[IniSection]) -> list[IniSection]:
    return [
        section
        for section in sections
        if section_has_endfield_13_payload(section)
        and not is_endfield_13_patch_section(section, sections)
    ]


def has_endfield_13_patch_for_target(sections: list[IniSection], target: IniSection) -> bool:
    patch_name = endfield_13_patch_section_name(target)
    return any(
        section_name_equals(section, patch_name)
        or (
            section_has_endfield_13_payload(section)
            and section.name.casefold() == patch_name.casefold()
        )
        for section in sections
    )


def restore_endfield_13_section_hash(lines: list[str], section: IniSection) -> int:
    changed = 0
    for line_index in range(section.start, section.end):
        raw_line = lines[line_index]
        match = _HASH_RE.match(raw_line.rstrip("\r\n"))
        if not match or match.group(1).lower() != END_FIELD_13_NEW_HASH:
            continue
        lines[line_index] = raw_line[:match.start(1)] + END_FIELD_13_OLD_HASH + raw_line[match.end(1):]
        changed += 1
    return changed


def build_endfield_13_block_lines(section_name: str, newline: str, leading_blank: str) -> list[str]:
    return [
        leading_blank,
        f"[{section_name}]{newline}",
        f"hash = {END_FIELD_13_NEW_HASH}{newline}",
        f"filter_index = {END_FIELD_13_FILTER_INDEX}{newline}",
        f"allow_duplicate_hash = {END_FIELD_13_DUPLICATE_POLICY}{newline}",
        newline,
    ]


def insert_endfield_13_block(lines: list[str], anchor: IniSection, newline: str) -> list[str]:
    insert_at = anchor.end
    while insert_at > anchor.start and not lines[insert_at - 1].strip():
        insert_at -= 1

    leading_blank = newline
    if insert_at > 0 and not lines[insert_at - 1].endswith(("\n", "\r")):
        leading_blank = newline + newline

    block_lines = build_endfield_13_block_lines(endfield_13_patch_section_name(anchor), newline, leading_blank)
    return lines[:insert_at] + block_lines + lines[anchor.end:]


def needs_endfield_13_stage(content: str) -> bool:
    lines = content.splitlines(keepends=True)
    sections = collect_sections(lines)

    if find_endfield_13_restore_sections(sections):
        return True

    return any(
        not has_endfield_13_patch_for_target(sections, target)
        for target in find_endfield_13_target_sections(sections)
    )


def apply_endfield_13_stage(content: str) -> tuple[str, StageResult]:
    original = content
    lines = content.splitlines(keepends=True)
    sections = collect_sections(lines)
    details: list[str] = []

    restored_sections = 0
    restored_hashes = 0
    for section in find_endfield_13_restore_sections(sections):
        restored = restore_endfield_13_section_hash(lines, section)
        if restored:
            restored_sections += 1
            restored_hashes += restored

    if restored_hashes:
        details.append(
            f"restored {restored_hashes} shader hash(es) in {restored_sections} section(s): "
            f"{END_FIELD_13_NEW_HASH} -> {END_FIELD_13_OLD_HASH}"
        )

    sections = collect_sections(lines)
    newline = detect_newline(content)
    inserted = 0

    for target in reversed(find_endfield_13_target_sections(sections)):
        if has_endfield_13_patch_for_target(sections, target):
            continue
        lines = insert_endfield_13_block(lines, target, newline)
        inserted += 1
        details.append(f"inserted {endfield_13_patch_section_name(target)} after {target.name}")
        sections = collect_sections(lines)

    new_content = "".join(lines)
    if inserted:
        details.insert(0, f"inserted {inserted} 1.3 shader override section(s)")
    return new_content, StageResult("1.3_fixer", new_content != original, details)


def apply_fixmenu_stage(content: str) -> tuple[str, StageResult]:
    count = content.count(FIXMENU_OLD_TOKEN)
    if count == 0:
        return content, StageResult("fixmenu2_ps_t", False, [f"{FIXMENU_OLD_TOKEN} not found"])

    content = content.replace(FIXMENU_OLD_TOKEN, FIXMENU_NEW_TOKEN)
    return content, StageResult(
        "fixmenu2_ps_t",
        True,
        [f"replaced {count} occurrence(s): {FIXMENU_OLD_TOKEN} -> {FIXMENU_NEW_TOKEN}"],
    )


def apply_correction_audit(content: str) -> tuple[str, StageResult]:
    has_fix_marker = LEGACY_PS_T_SHIFT_MARKER in content or END_FIELD_FIXED_MARKER in content
    if not has_fix_marker:
        return content, StageResult("correction_audit", False, [])

    lines = content.splitlines(keepends=True)
    sections = collect_sections(lines)
    changed = 0
    duplicate_diffuse_changes = 0
    body_blue_glow_changes = 0
    hair_overshift_changes = 0
    legacy_nonconditional_overshift_changes = 0
    diffuse13_normal16_no_light_changes = 0

    for section in sections:
        has_ps_t0 = False
        ps_t16_resources: list[str] = []
        lightmap_slots: set[int] = set()
        normalmap_slots: set[int] = set()
        slot_resources: dict[int, str] = {}
        section_text = (section.name + "\n" + "".join(section.lines)).lower()
        body_tokens = (
            "body",
            "skin",
            "\u8eab\u4f53",
            "\u8eab\u9ad4",
            "\u76ae\u80a4",
            "\u808c\u80a4",
        )
        hair_tokens = (
            "hair",
            "\u5934\u53d1",
            "\u982d\u9aee",
            "\u9aee",
        )
        body_like_section = any(token in section_text for token in body_tokens)
        hair_like_section = any(token in section_text for token in hair_tokens)
        raw_section_lines = [line.rstrip("\r\n") for line in section.lines]
        has_conditional_textures = section_has_conditional_texture_bindings(raw_section_lines)

        for raw_line in section.lines:
            stripped = raw_line.strip()
            if stripped.startswith(";"):
                continue
            if re.match(r"ps-t0\s*=", stripped, flags=re.IGNORECASE):
                has_ps_t0 = True
            m_slot = re.match(r"ps-t(\d+)\s*=\s*(\S+)", stripped, flags=re.IGNORECASE)
            if not m_slot:
                continue
            slot = int(m_slot.group(1))
            resource = m_slot.group(2).lower()
            slot_resources[slot] = resource
            if slot == 16:
                ps_t16_resources.append(resource)
            if "lightmap" in resource:
                lightmap_slots.add(slot)
            if "normalmap" in resource:
                normalmap_slots.add(slot)

        diffuse13_normal16_no_light_pattern = (
            "diffusemap" in slot_resources.get(13, "")
            and "normalmap" in slot_resources.get(16, "")
            and not any("lightmap" in resource for resource in slot_resources.values())
        )
        legacy_nonconditional_overshift_pattern = (
            LEGACY_PS_T_SHIFT_MARKER in content
            and not has_conditional_textures
            and (
                any(
                    ("diffusemap" in resource and slot in {4, 15, 16})
                    or ("lightmap" in resource and slot == 17)
                    or ("normalmap" in resource and slot in {17, 18})
                    for slot, resource in slot_resources.items()
                )
                or diffuse13_normal16_no_light_pattern
            )
        )

        if legacy_nonconditional_overshift_pattern:
            for line_index in range(section.start, section.end):
                raw_line = lines[line_index]
                line_body = raw_line.rstrip("\r\n")
                line_end = raw_line[len(line_body):]
                m_legacy = re.match(r"^(\s*ps-t)(\d+)(\s*=\s*)(\S+.*)$", line_body, flags=re.IGNORECASE)
                if not m_legacy:
                    continue
                slot = int(m_legacy.group(2))
                resource = m_legacy.group(4).lower()
                should_rollback = (
                    ("diffusemap" in resource and slot in {4, 15, 16})
                    or ("lightmap" in resource and slot in {16, 17})
                    or ("normalmap" in resource and slot in {17, 18})
                    or ("normalmap" in resource and slot == 16 and diffuse13_normal16_no_light_pattern)
                )
                if not should_rollback:
                    continue
                if "normalmap" in resource and slot == 16 and diffuse13_normal16_no_light_pattern:
                    diffuse13_normal16_no_light_changes += 1
                new_slot = slot - 2
                lines[line_index] = f"{m_legacy.group(1)}{new_slot}{m_legacy.group(3)}{m_legacy.group(4)}{line_end}"
                changed += 1
                legacy_nonconditional_overshift_changes += 1
            continue

        hair_overshift_pattern = (
            hair_like_section
            and 14 not in slot_resources
            and 15 not in slot_resources
            and "diffusemap" in slot_resources.get(16, "")
            and "lightmap" in slot_resources.get(17, "")
            and "normalmap" in slot_resources.get(18, "")
        )

        if hair_overshift_pattern:
            for line_index in range(section.start, section.end):
                raw_line = lines[line_index]
                line_body = raw_line.rstrip("\r\n")
                line_end = raw_line[len(line_body):]
                m_hair = re.match(r"^(\s*ps-t)(1[678])(\s*=\s*)(\S+.*)$", line_body, flags=re.IGNORECASE)
                if not m_hair:
                    continue
                new_slot = int(m_hair.group(2)) - 2
                lines[line_index] = f"{m_hair.group(1)}{new_slot}{m_hair.group(3)}{m_hair.group(4)}{line_end}"
                changed += 1
                hair_overshift_changes += 1
            continue

        if has_ps_t0:
            continue

        for line_index in range(section.start, section.end):
            raw_line = lines[line_index]
            line_body = raw_line.rstrip("\r\n")
            line_end = raw_line[len(line_body):]
            m2 = re.match(r"^(\s*)ps-t2(\s*=\s*)(\S+)(.*)$", line_body, flags=re.IGNORECASE)
            if not m2:
                continue

            resource = m2.group(3)
            resource_key = resource.lower()
            if "diffusemap" not in resource_key:
                continue
            duplicate_shifted_diffuse = any(candidate.startswith(resource_key) for candidate in ps_t16_resources)
            body_blue_glow_pattern = body_like_section and (
                (17 in lightmap_slots and 18 in normalmap_slots)
                or (not lightmap_slots and 16 in normalmap_slots)
            )
            if not duplicate_shifted_diffuse and not body_blue_glow_pattern:
                continue

            lines[line_index] = f"{m2.group(1)}ps-t0{m2.group(2)}{resource}{m2.group(4)}{line_end}"
            changed += 1
            if duplicate_shifted_diffuse:
                duplicate_diffuse_changes += 1
            elif body_blue_glow_pattern:
                body_blue_glow_changes += 1

    if not changed:
        return content, StageResult("correction_audit", False, [])

    primary_diffuse_changes = duplicate_diffuse_changes + body_blue_glow_changes
    details = [f"applied {changed} correction(s)"]
    if primary_diffuse_changes:
        details.append(f"restored {primary_diffuse_changes} suspicious primary DiffuseMap binding(s): ps-t2 -> ps-t0")
    if duplicate_diffuse_changes:
        details.append(f"duplicate shifted DiffuseMap pattern: {duplicate_diffuse_changes}")
    if body_blue_glow_changes:
        details.append(f"body blue-glow fallback pattern: {body_blue_glow_changes}")
    if hair_overshift_changes:
        details.append(f"hair over-shift rollback: {hair_overshift_changes}")
    if legacy_nonconditional_overshift_changes:
        details.append(f"legacy non-conditional over-shift rollback: {legacy_nonconditional_overshift_changes}")
    if diffuse13_normal16_no_light_changes:
        details.append(
            f"skin/no-light NormalMap rollback: {diffuse13_normal16_no_light_changes} (ps-t16 -> ps-t14)"
        )

    return "".join(lines), StageResult(
        "correction_audit",
        True,
        details,
    )


def line_matches_marker(line: str, marker_re: re.Pattern[str]) -> bool:
    return bool(marker_re.match(line.rstrip("\r\n")))


def remove_legacy_marker_lines(content: str) -> tuple[str, dict[str, int]]:
    lines = content.splitlines(keepends=True)
    removed = {
        LEGACY_ENDFIELD_SOURCE: 0,
        LEGACY_PS_T_LINE_SOURCE: 0,
    }
    out_lines: list[str] = []

    for line in lines:
        if line_matches_marker(line, END_FIELD_FIXED_MARKER_RE):
            removed[LEGACY_ENDFIELD_SOURCE] += 1
            continue
        if line_matches_marker(line, LEGACY_PS_T_SHIFT_MARKER_RE):
            removed[LEGACY_PS_T_LINE_SOURCE] += 1
            continue
        out_lines.append(line)

    return "".join(out_lines), removed


def apply_legacy_marker_cleanup(content: str, legacy_sources: set[str]) -> tuple[str, StageResult]:
    new_content, removed = remove_legacy_marker_lines(content)
    details = [
        f"detected {source}"
        for source in (
            LEGACY_EFMI_SOURCE,
            LEGACY_ENDFIELD_SOURCE,
            LEGACY_PS_T_SOURCE,
            LEGACY_PS_T_LINE_SOURCE,
        )
        if source in legacy_sources
    ]
    details.extend(
        f"removed {count} {source} line(s)"
        for source, count in removed.items()
        if count
    )

    return new_content, StageResult("legacy_marker_cleanup", new_content != content, details)


def collect_hash_values(content: str) -> set[str]:
    values: set[str] = set()
    for line in content.splitlines():
        match = _HASH_RE.match(line)
        if match:
            values.add(match.group(1).lower())
    return values


def detect_new_version_mod(content: str, mapping: HashMapping) -> tuple[bool, str]:
    hash_values = collect_hash_values(content)
    if not hash_values:
        return False, ""

    efmi_old_hits = hash_values.intersection(mapping._map.keys())
    efmi_new_hashes = set(mapping._map.values()).union(mapping._index_counts.keys())
    efmi_new_hits = hash_values.intersection(efmi_new_hashes)
    shader_old_hits = hash_values.intersection(h.lower() for h in OLD_SHADER_HASHES)
    shader_new_hits = hash_values.intersection(h.lower() for h in NEW_SHADER_HASHES)

    has_match_index_count = any(_MIC_RE.match(line) for line in content.splitlines())
    has_overrule = "allow_duplicate_hash = overrule" in content.lower()

    if END_FIELD_FIXED_MARKER in content:
        return True, "endfield fixed marker already present"

    if LEGACY_PS_T_SHIFT_MARKER in content:
        return True, "legacy ps-t-shifted marker already present"

    if shader_new_hits and not shader_old_hits and has_overrule:
        return True, f"new ShaderOverride hashes detected ({len(shader_new_hits)})"

    if efmi_new_hits and has_match_index_count and not efmi_old_hits:
        return True, f"new EFMI hashes with match_index_count detected ({len(efmi_new_hits)})"

    return False, ""


def add_required_stage(stages: list[str], stage_name: str) -> None:
    if stage_name not in stages:
        stages.append(stage_name)


def ps_t_shift_signature(content: str) -> list[tuple[int, str]]:
    signature: list[tuple[int, str]] = []
    lines = content.splitlines(keepends=True)
    for section in collect_sections(lines):
        filter_index = extract_filter_index(section)
        if filter_index not in SUPPORTED_FILTERS:
            continue
        target_section_re = re.compile(rf"^{re.escape(SECTION_PREFIX)}\d+$", re.IGNORECASE)
        if not target_section_re.match(section.name):
            continue
        for raw_line in section.lines:
            match = _HASH_RE.match(raw_line.rstrip("\r\n"))
            if match:
                signature.append((filter_index, match.group(1).lower()))
                break
    return sorted(signature)


def expected_ps_t_shift_signature(use_13_hash: bool) -> list[tuple[int, str]]:
    signature: list[tuple[int, str]] = []
    for filter_index, hashes in HASH_RULES.items():
        for hash_value in hashes:
            normalized = hash_value.lower()
            if use_13_hash and normalized == END_FIELD_13_OLD_HASH:
                normalized = END_FIELD_13_NEW_HASH
            signature.append((filter_index, normalized))
    return sorted(signature)


def needs_ps_t_shift_stage(content: str) -> bool:
    signature = ps_t_shift_signature(content)
    if not signature:
        return False
    return signature not in (
        expected_ps_t_shift_signature(use_13_hash=False),
        expected_ps_t_shift_signature(use_13_hash=True),
    )


def detect_required_stages(content: str, mapping: HashMapping) -> tuple[str, ...]:
    hash_values = collect_hash_values(content)
    required: list[str] = []

    efmi_old_hits = hash_values.intersection(mapping._map.keys())
    shader_old_hits = hash_values.intersection(h.lower() for h in OLD_SHADER_HASHES)

    if efmi_old_hits:
        add_required_stage(required, "EFMI_Fix_F")

    if shader_old_hits or needs_endfield_fix2(content):
        add_required_stage(required, "endfield_mod_fix")

    if needs_ps_t_shift_stage(content):
        add_required_stage(required, "ps_t_shift")

    if needs_endfield_13_stage(content) or "ps_t_shift" in required:
        add_required_stage(required, "1.3_fixer")

    return tuple(required)


def process_text(
    content: str,
    mapping: HashMapping,
    pattern: re.Pattern[str],
    skip_new_version: bool = True,
    enable_fixmenu: bool = False,
    legacy_sources: set[str] | None = None,
) -> tuple[str, list[StageResult]]:
    legacy_sources = legacy_sources or set()
    pre_stages: list[StageResult] = []

    content, stage = apply_correction_audit(content)
    if stage.changed:
        pre_stages.append(stage)

    content, stage = apply_legacy_marker_cleanup(content, legacy_sources)
    if stage.changed:
        pre_stages.append(stage)

    if skip_new_version:
        required_stages = detect_required_stages(content, mapping)
    else:
        required_stages = ("EFMI_Fix_F", "endfield_mod_fix", "ps_t_shift", "1.3_fixer")

    newline = detect_newline(content)
    stages: list[StageResult] = pre_stages

    if "EFMI_Fix_F" in required_stages:
        content, stage = apply_efmi_hash_stage(content, mapping, pattern, newline)
        stages.append(stage)

    if "endfield_mod_fix" in required_stages:
        newline = detect_newline(content)
        content, stage = apply_endfield_stage(content, newline)
        stages.append(stage)

    if "ps_t_shift" in required_stages:
        newline = detect_newline(content)
        content, stage = apply_ps_t_shift_stage(content, newline)
        stages.append(stage)

    if "1.3_fixer" in required_stages or needs_endfield_13_stage(content):
        content, stage = apply_endfield_13_stage(content)
        stages.append(stage)

    content, stage = apply_correction_audit(content)
    if stage.changed:
        stages.append(stage)

    if enable_fixmenu:
        content, stage = apply_fixmenu_stage(content)
        stages.append(stage)

    return content, stages


def is_disabled_ini(path: Path) -> bool:
    return path.name.upper().startswith(DISABLED_PREFIX)


def is_hidden_path(relpath: Path) -> bool:
    return any(part.startswith(".") for part in relpath.parts[:-1])


def iter_ini_files(root: Path, include_disabled: bool) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.ini"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if is_hidden_path(rel):
            continue
        if OLD_BACKUP_NAME_RE.search(path.name):
            continue
        if is_disabled_ini(path) and not include_disabled:
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p).lower())


def path_identity(path: Path) -> str:
    try:
        return str(path.resolve()).casefold()
    except OSError:
        return str(path.absolute()).casefold()


def collect_unified_backup_identities(root: Path) -> set[str]:
    identities: set[str] = set()
    for session in list_backup_sessions(root):
        manifest_path = session / BACKUP_MANIFEST
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for entry in manifest.get("files", []):
            for key in ("backup_rel", "before_rel", "after_rel"):
                rel = entry.get(key)
                if rel:
                    identities.add(path_identity(root / rel))
    return identities


def has_legacy_efmi_backup(path: Path, unified_backup_identities: set[str]) -> bool:
    pattern = f"{path.name}.backup.*"
    for backup in path.parent.glob(pattern):
        if not backup.is_file():
            continue
        if not OLD_BACKUP_NAME_RE.search(backup.name):
            continue
        if path_identity(backup) in unified_backup_identities:
            continue
        return True
    return False


def has_ps_t_shift_disabled_backup(path: Path) -> bool:
    direct = path.with_name(f"{DISABLED_PREFIX}{path.name}")
    if direct.is_file():
        return True

    pattern = re.compile(
        rf"^{re.escape(DISABLED_PREFIX)}{re.escape(path.stem)}(?:\.\d+)?{re.escape(path.suffix)}$",
        re.IGNORECASE,
    )
    return any(candidate.is_file() and pattern.match(candidate.name) for candidate in path.parent.iterdir())


def detect_legacy_fix_sources(path: Path, content: str, unified_backup_identities: set[str]) -> set[str]:
    sources: set[str] = set()

    if any(line_matches_marker(line, END_FIELD_FIXED_MARKER_RE) for line in content.splitlines()):
        sources.add(LEGACY_ENDFIELD_SOURCE)
    if any(line_matches_marker(line, LEGACY_PS_T_SHIFT_MARKER_RE) for line in content.splitlines()):
        sources.add(LEGACY_PS_T_LINE_SOURCE)
    if has_legacy_efmi_backup(path, unified_backup_identities):
        sources.add(LEGACY_EFMI_SOURCE)
    if has_ps_t_shift_disabled_backup(path):
        sources.add(LEGACY_PS_T_SOURCE)

    return sources


def resolve_mods_root(root: Path) -> Path:
    for path in [root, *root.parents]:
        if path.name.casefold() == MODS_DIR_NAME.casefold():
            return path

    child_mods = root / MODS_DIR_NAME
    if child_mods.is_dir():
        return child_mods.resolve()

    runtime_base = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
    for path in [runtime_base, *runtime_base.parents]:
        if path.name.casefold() == MODS_DIR_NAME.casefold():
            return path

    return root


def iter_hotfix_cleanup_files(root: Path) -> list[Path]:
    files: list[Path] = []
    seen_files: set[str] = set()
    for path in root.rglob("*.ini"):
        if not path.is_file():
            continue
        if path.name.casefold() != HOTFIX_INI_NAME.casefold():
            continue
        key = path_identity(path)
        if key in seen_files:
            continue
        seen_files.add(key)
        rel = path.relative_to(root)
        if is_hidden_path(rel):
            continue
        files.append(path)

    return sorted(files, key=lambda p: str(p).lower())


def display_relpath(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def delete_hotfix_files(root: Path, files: list[Path]) -> int:
    deleted = 0
    for path in files:
        relpath = display_relpath(root, path)
        try:
            path.unlink()
        except FileNotFoundError:
            print(f"[DELETE-SKIP] {relpath} already missing")
            continue
        deleted += 1
        print(f"[DELETE] {relpath}")
    return deleted


def manifest_relpath(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def sidecar_backup_path(path: Path, marker: str, suffix: str = "") -> Path:
    candidate = path.with_name(f"{path.name}.backup.{marker}{suffix}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.backup.{marker}{suffix}.{counter}")
        counter += 1
    return candidate


def make_session_dir(root: Path, label: str | None = None) -> Path:
    backup_root = root / BACKUP_DIR_NAME
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"{timestamp}_{label}" if label else timestamp
    session = backup_root / session_name
    counter = 1
    while session.exists():
        session = backup_root / f"{session_name}_{counter}"
        counter += 1
    session.mkdir(parents=True)
    return session


def list_backup_sessions(root: Path) -> list[Path]:
    backup_root = root / BACKUP_DIR_NAME
    if not backup_root.exists():
        return []
    sessions = [p for p in backup_root.iterdir() if p.is_dir() and (p / BACKUP_MANIFEST).exists()]
    return sorted(sessions, key=lambda p: p.name)


def resolve_manifest_source(root: Path, session: Path, entry: dict[str, Any], *keys: str) -> Path:
    for key in keys:
        rel = entry.get(key)
        if not rel:
            continue
        candidates = [root / rel, session / rel]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]
    return session / "files" / Path(entry["path"])


def resolve_manifest_backup_source(root: Path, session: Path, entry: dict[str, Any]) -> Path:
    return resolve_manifest_source(root, session, entry, "before_rel", "backup_rel")


def resolve_manifest_restore_source(
    root: Path,
    session: Path,
    entry: dict[str, Any],
    restore_before: bool,
) -> tuple[Path, str]:
    if restore_before:
        return resolve_manifest_source(root, session, entry, "before_rel", "backup_rel"), "before"
    if entry.get("after_rel"):
        return resolve_manifest_source(root, session, entry, "after_rel"), "after"
    return resolve_manifest_source(root, session, entry, "before_rel", "backup_rel"), "before"


def make_backup_session(root: Path, plans: list[FilePlan]) -> Path:
    session = make_session_dir(root)

    manifest_files: list[dict[str, Any]] = []
    for plan in plans:
        backup_path = sidecar_backup_path(plan.path, session.name)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan.path, backup_path)
        backup_rel = manifest_relpath(root, backup_path)
        manifest_files.append({
            "path": plan.relpath,
            "backup_rel": backup_rel,
            "before_rel": backup_rel,
            "backup_name": backup_path.name,
            "before_name": backup_path.name,
            "encoding": plan.encoding,
            "stages": [
                {"name": stage.name, "details": stage.details, "hits": len(stage.hits)}
                for stage in plan.stages if stage.changed
            ],
        })

    manifest = {
        "schema": 2,
        "operation": "fix",
        "completed": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "files": manifest_files,
    }
    (session / BACKUP_MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return session


def write_plans(plans: list[FilePlan], backup_session: Path) -> None:
    written: list[FilePlan] = []
    try:
        for plan in plans:
            plan.path.write_bytes(plan.new_text.encode(plan.encoding))
            written.append(plan)
    except Exception:
        manifest = json.loads((backup_session / BACKUP_MANIFEST).read_text(encoding="utf-8"))
        root = Path(manifest["root"])
        backup_map = {
            entry["path"]: resolve_manifest_backup_source(root, backup_session, entry)
            for entry in manifest.get("files", [])
        }
        for written_plan in written:
            backup_path = backup_map.get(written_plan.relpath)
            if backup_path is not None and backup_path.exists():
                shutil.copy2(backup_path, written_plan.path)
        raise


def finalize_backup_session(root: Path, backup_session: Path, plans: list[FilePlan]) -> None:
    manifest_path = backup_session / BACKUP_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {entry["path"]: entry for entry in manifest.get("files", [])}

    for plan in plans:
        after_path = sidecar_backup_path(plan.path, backup_session.name, ".after")
        after_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan.path, after_path)
        entry = entries.get(plan.relpath)
        if entry is None:
            continue
        entry["after_rel"] = manifest_relpath(root, after_path)
        entry["after_name"] = after_path.name

    manifest["completed"] = True
    manifest["completed_at"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def find_backup_session(root: Path, backup_id: str) -> Path:
    backup_root = root / BACKUP_DIR_NAME
    if not backup_root.exists():
        raise FileNotFoundError(f"No backup directory found: {backup_root}")

    sessions = list_backup_sessions(root)
    if not sessions:
        raise FileNotFoundError(f"No backup sessions found under: {backup_root}")

    if backup_id.lower() == "latest":
        return sessions[-1]

    exact = backup_root / backup_id
    if exact.exists() and (exact / BACKUP_MANIFEST).exists():
        return exact

    if backup_id.isdecimal():
        index = int(backup_id)
        if 1 <= index <= len(sessions):
            return sessions[index - 1]
        raise FileNotFoundError(f"Backup number not found: {backup_id}")

    matches = [p for p in sessions if p.name.startswith(backup_id)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Backup id {backup_id!r} is ambiguous: {', '.join(p.name for p in matches)}")
    raise FileNotFoundError(f"Backup id not found: {backup_id}")


def make_current_snapshot_session(root: Path, entries: list[dict[str, Any]], reason: str) -> Path | None:
    existing: list[tuple[dict[str, Any], Path]] = []
    for entry in entries:
        path = root / entry["path"]
        if path.exists() and path.is_file():
            existing.append((entry, path))
    if not existing:
        return None

    session = make_session_dir(root, "rollback")
    manifest_files: list[dict[str, Any]] = []
    for entry, path in existing:
        snapshot_path = sidecar_backup_path(path, session.name)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, snapshot_path)
        snapshot_rel = manifest_relpath(root, snapshot_path)
        manifest_files.append({
            "path": entry["path"],
            "backup_rel": snapshot_rel,
            "before_rel": snapshot_rel,
            "after_rel": snapshot_rel,
            "backup_name": snapshot_path.name,
            "before_name": snapshot_path.name,
            "after_name": snapshot_path.name,
            "encoding": entry.get("encoding"),
            "stages": [{"name": "rollback_snapshot", "details": [reason], "hits": 0}],
        })

    manifest = {
        "schema": 2,
        "operation": "rollback_snapshot",
        "completed": True,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "files": manifest_files,
    }
    (session / BACKUP_MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return session


def files_differ(dest: Path, src: Path) -> bool:
    try:
        return not dest.exists() or dest.read_bytes() != src.read_bytes()
    except OSError:
        return True


def rollback(root: Path, backup_id: str, restore_before: bool = False) -> int:
    session = find_backup_session(root, backup_id)
    manifest = json.loads((session / BACKUP_MANIFEST).read_text(encoding="utf-8"))
    restore_items: list[tuple[dict[str, Any], Path, Path, str]] = []
    fallback_to_before = 0

    for entry in manifest.get("files", []):
        dest = root / entry["path"]
        src, state = resolve_manifest_restore_source(root, session, entry, restore_before)
        if not src.exists():
            print(f"[SKIP] Missing backup file: {src}")
            continue
        if not restore_before and state == "before":
            fallback_to_before += 1
        restore_items.append((entry, dest, src, state))

    if not restore_items:
        print(f"No restorable files found in backup session: {session.name}")
        return 1

    snapshot_session: Path | None = None
    if any(files_differ(dest, src) for _, dest, src, _ in restore_items):
        snapshot_session = make_current_snapshot_session(
            root,
            [entry for entry, _, _, _ in restore_items],
            f"current state before restoring {session.name}",
        )

    restored = 0
    for entry, dest, src, state in restore_items:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        restored += 1
        print(f"[RESTORED-{state.upper()}] {entry['path']}")

    if fallback_to_before:
        print(f"[WARN] {fallback_to_before} file(s) had no after snapshot; restored their before snapshot instead.")
    if snapshot_session is not None:
        print(f"Current state snapshot: {snapshot_session.name}")
    mode = "before" if restore_before else "after"
    print(f"\nRollback complete from {session.name} ({mode} state): restored {restored} file(s).")
    return 0


def list_backups(root: Path) -> int:
    backup_root = root / BACKUP_DIR_NAME
    if not backup_root.exists():
        print(f"No backup directory found: {backup_root}")
        return 0
    sessions = list_backup_sessions(root)
    if not sessions:
        print(f"No backup sessions found under: {backup_root}")
        return 0
    for index, session in enumerate(sessions, start=1):
        try:
            manifest = json.loads((session / BACKUP_MANIFEST).read_text(encoding="utf-8"))
            file_count = len(manifest.get("files", []))
            created = manifest.get("created_at", session.name)
            operation = manifest.get("operation", "legacy")
            has_after = any(entry.get("after_rel") for entry in manifest.get("files", []))
            state = "after" if has_after else "before-only"
            if manifest.get("completed") is False:
                state += ", incomplete"
        except Exception:
            file_count = 0
            created = session.name
            operation = "unreadable"
            state = "unknown"
        print(f"[{index}] {session.name} | {file_count} file(s) | {created} | {operation} | {state}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified EFMI ini fixer with backup and rollback.")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan. Defaults to current directory.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files or creating backups.")
    parser.add_argument("--include-disabled", action="store_true", help="Also process DISABLED*.ini files.")
    parser.add_argument("--force-new-version", action="store_true", help="Run fixes even when an ini looks like a newer-version mod.")
    parser.add_argument("--fixmenu", "--enable-fixmenu", dest="enable_fixmenu", action="store_true", help="Enable optional fixmenu2.0 ps-t102 -> ps-t100 replacement stage.")
    parser.add_argument("--list-backups", action="store_true", help="List available backup sessions and exit.")
    parser.add_argument("--rollback", nargs="?", const="latest", metavar="ID", help="Restore to the after-state of backup ID/number, or latest if ID is omitted.")
    parser.add_argument("--restore", dest="rollback", nargs="?", const="latest", metavar="ID", help="Alias for --rollback.")
    parser.add_argument("--rollback-before", action="store_true", help="Restore the before-state of the selected backup instead of its after-state.")
    return parser


def runtime_command_name() -> str:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).name
    return f"python {Path(__file__).name}"


def validate_root(root: Path) -> int | None:
    if not root.exists():
        print(f"[ERROR] Root path does not exist: {root}")
        return 1
    if not root.is_dir():
        print(f"[ERROR] Root path is not a directory: {root}")
        return 1
    return None


def ensure_hash_rules() -> bool:
    total_hashes = sum(len(values) for values in HASH_RULES.values())
    if total_hashes == 0:
        print("[ERROR] HASH_RULES is empty; ps_t_shift stage would remove target sections.")
        return False
    return True


def build_processing_context() -> tuple[HashMapping, re.Pattern[str]]:
    mapping = HashMapping.from_characters(CHARACTERS)
    pattern = mapping.pattern()
    return mapping, pattern


def build_fix_plan(options: RunOptions, mapping: HashMapping, pattern: re.Pattern[str]) -> FixPlan:
    root = options.root
    hotfix_root = resolve_mods_root(root)
    hotfix_files = iter_hotfix_cleanup_files(hotfix_root)
    hotfix_file_keys = {path_identity(path) for path in hotfix_files}
    unified_backup_identities = collect_unified_backup_identities(root)
    ini_files = [
        path
        for path in iter_ini_files(root, include_disabled=options.include_disabled)
        if path_identity(path) not in hotfix_file_keys
    ]
    print(f"Scanning {len(ini_files)} .ini file(s) under: {root}")

    file_plans: list[FilePlan] = []
    skipped_new_version = 0
    for path in ini_files:
        relpath = str(path.relative_to(root)).replace("\\", "/")
        try:
            original_text, encoding = load_text(path)
            legacy_sources = detect_legacy_fix_sources(path, original_text, unified_backup_identities)
            new_text, stages = process_text(
                original_text,
                mapping,
                pattern,
                skip_new_version=not options.force_new_version,
                enable_fixmenu=options.enable_fixmenu,
                legacy_sources=legacy_sources,
            )
        except Exception as exc:
            print(f"[ERROR] {relpath}: {exc}")
            continue

        if stages and stages[0].name == "new_version_guard" and not any(stage.changed for stage in stages):
            skipped_new_version += 1
            print(f"[SKIP-NEW] {relpath} | {stages[0].details[0]}")
            continue

        plan = FilePlan(path=path, relpath=relpath, original_text=original_text, new_text=new_text, encoding=encoding, stages=stages)
        if plan.changed:
            file_plans.append(plan)
            visible_stages = [
                stage for stage in stages
                if stage.changed and stage.name not in SILENT_STAGE_NAMES
            ]
            if not visible_stages:
                continue
            status = "DRY-RUN" if options.dry_run else "PENDING"
            print(f"[{status}] {relpath}")
            for stage in visible_stages:
                print(f"  - {stage.name}: {'; '.join(stage.details) if stage.details else 'changed'}")

    for path in hotfix_files:
        relpath = display_relpath(hotfix_root, path)
        status = "DRY-RUN" if options.dry_run else "PENDING"
        print(f"[{status}] {relpath}")
        print(f"  - hotfix_cleanup: hard delete {HOTFIX_INI_NAME}")

    return FixPlan(
        root=root,
        hotfix_root=hotfix_root,
        file_plans=file_plans,
        hotfix_files=hotfix_files,
        skipped_new_version=skipped_new_version,
    )


def skipped_suffix(skipped_new_version: int) -> str:
    return f" 已跳过 {skipped_new_version} 个较新版本文件。" if skipped_new_version else ""


def finish_no_changes(plan: FixPlan) -> int:
    suffix = skipped_suffix(plan.skipped_new_version)
    print(f"\n完成。无需修改。{suffix}")
    return 0


def finish_dry_run(plan: FixPlan) -> int:
    suffix = skipped_suffix(plan.skipped_new_version)
    total_changes = len(plan.file_plans) + len(plan.hotfix_files)
    print(f"\n预览扫描完成。将修改/删除 {total_changes} 个文件。{suffix} 未创建备份。")
    return 0


def execute_fix_plan(plan: FixPlan) -> int:
    root = plan.root
    backup_session: Path | None = None
    if plan.file_plans:
        try:
            backup_session = make_backup_session(root, plan.file_plans)
        except Exception as exc:
            print(f"[ERROR] 无法创建备份会话：{exc}")
            return 1

        try:
            write_plans(plan.file_plans, backup_session)
        except Exception as exc:
            print(f"[ERROR] 写入失败；已从备份恢复已经写入的文件：{exc}")
            print(f"已保留备份会话：{backup_session}")
            return 1

        try:
            finalize_backup_session(root, backup_session, plan.file_plans)
        except Exception as exc:
            print(f"[ERROR] 修改已写入，但创建修复后状态备份失败：{exc}")
            print(f"已保留修复前状态备份会话：{backup_session}")
            return 1

    try:
        deleted_hotfixes = delete_hotfix_files(plan.hotfix_root, plan.hotfix_files)
    except Exception as exc:
        print(f"[ERROR] 热修复清理失败：{exc}")
        if backup_session is not None:
            print(f"已保留备份会话：{backup_session}")
        return 1

    print(f"\n完成。已修改 {len(plan.file_plans)} 个文件，已硬删除 {deleted_hotfixes} 个热修复文件。")
    if backup_session is not None:
        print(f"备份会话：{backup_session.name}")
        command_name = runtime_command_name()
        print(f"恢复到本次修复后状态：{command_name} {root} --rollback {backup_session.name}")
        print(f"撤销本次修复：{command_name} {root} --rollback {backup_session.name} --rollback-before")
    else:
        print("未创建备份会话，因为本次只执行了硬删除清理。")
    return 0


def run_fix(options: RunOptions) -> int:
    if not ensure_hash_rules():
        return 1

    mapping, pattern = build_processing_context()
    plan = build_fix_plan(options, mapping, pattern)

    if not plan.file_plans and not plan.hotfix_files:
        return finish_no_changes(plan)

    if options.dry_run:
        return finish_dry_run(plan)

    return execute_fix_plan(plan)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    root = Path(args.root).resolve()

    validation_error = validate_root(root)
    if validation_error is not None:
        return validation_error

    if args.list_backups:
        return list_backups(root)
    if args.rollback:
        return rollback(root, args.rollback, restore_before=args.rollback_before)

    return run_fix(
        RunOptions(
            root=root,
            dry_run=args.dry_run,
            include_disabled=args.include_disabled,
            force_new_version=args.force_new_version,
            enable_fixmenu=args.enable_fixmenu,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
