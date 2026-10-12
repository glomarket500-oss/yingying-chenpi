# -*- coding: utf-8 -*-
import sys
from opencc import OpenCC
cc = OpenCC('s2hk')
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
out = cc.convert(t)
# 品牌名修正：OpenCC 會把「滢」轉成「瀅」，本站一律用「滢滢」
out = out.replace('瀅', '滢')
open(dst, 'w', encoding='utf-8').write(out)
print(f'converted {len(t)} -> {len(out)} chars')
