import unicodedata

import MeCab
from jaconv import jaconv


def is_kanji(ch):
    return 'CJK UNIFIED IDEOGRAPH' in unicodedata.name(ch)


def is_hiragana(ch):
    return 'HIRAGANA' in unicodedata.name(ch)

def okurigana_process(text, hiragana):
    back = []
    front = []
    text_pointer = [0, len(text) - 1]
    kana_pointer = [0, len(hiragana) - 1]
    while text_pointer[0] <= text_pointer[1]:
        if not is_kanji(text[text_pointer[0]]):
            front.append((text[text_pointer[0]],))
            text_pointer[0] += 1
            kana_pointer[0] += 1
        else:
            break
    while text_pointer[0] <= text_pointer[1]:
        if not is_kanji(text[text_pointer[1]]):
            back.append((text[text_pointer[1]],))
            text_pointer[1] -= 1
            kana_pointer[1] -= 1
        else:
            break
    if text_pointer[0] <= text_pointer[1]:
        # Should handle the parts of a certain kanji, with special method
        if(text_pointer[1] - text_pointer[0] == kana_pointer[1] - kana_pointer[0]):
            front.extend([(text[i], hiragana[i]) for i in range(text_pointer[0], text_pointer[1] + 1)])
        else:
            front.append((text[text_pointer[0]:text_pointer[1] + 1], hiragana[kana_pointer[0]:kana_pointer[1] + 1]))
    front.extend(back[::-1])
    return front

def split_furigana(text):
    """ MeCab has a problem if used inside a generator ( use yield instead of return  )
    The error message is:
    ```
    SystemError: <built-in function delete_Tagger> returned a result with an error set
    ```
    It seems like MeCab has bug in releasing resource
    """

    dicdir = '-d /opt/homebrew/lib/mecab/dic/unidic'
    mecab = MeCab.Tagger(dicdir)
    mecab.parse('') # 空でパースする必要がある
    node = mecab.parseToNode(text)
    ret = []

    while node is not None:
        origin = node.surface # もとの単語を代入
        if not origin or origin == "":
            node = node.next
            continue
        print(origin, node.feature)
        # originが空のとき、漢字以外の時はふりがなを振る必要がないのでそのまま出力する
        if any(is_kanji(_) for _ in origin):
            #sometimes MeCab can't give kanji reading, and make node-feature have less than 9 when splitted.
            #bypass it and give kanji as isto avoid IndexError
            # print(origin, node.feature)
            if len(node.feature.split(",")) > 9:
                kana = node.feature.split(",")[9] # 読み仮名を代入
            else:
                kana = node.surface
            hiragana = jaconv.kata2hira(kana)
            # print(origin, kana, hiragana)
            ret += okurigana_process(origin, hiragana)
        else:
            if origin:
                ret += [(origin,)]
        node = node.next
    return ret


def print_html(text, file=None):
    furigana = split_furigana(text)
    print(furigana)
    for pair in furigana:
        if len(pair)==2:
            kanji,hira = pair
            print("<ruby><rb>{0}</rb><rt>{1}</rt></ruby>".
                    format(kanji, hira), end='', file=file)
        else:
            print(pair[0], end='', file=file)
    print('', file=file)


def print_plaintext(text, file=None):
    for pair in split_furigana(text)[0]:
        if len(pair) == 2:
            kanji,hira = pair
            print("%s(%s)" % (kanji,hira), end='', file=file)
        else:
            print(pair[0], end='',file=file)
    print('', file=file)


def main():
    text = '澱んだ街角で,僕らは出会った'
    # text = '活版印刷の流れを汲む出版作業では'
    # text = 'お茶にお煎餅、よく合いますね'
    # text = '野ブタ。をプロデュース'
    # text = '本当に'
    # text = '平気'
    # text = '平然'
    # text = '格好いい'
    # text = '庭には２羽鶏がいる'
    with open('tmp.html', 'w') as buffer:
        print_html(text,buffer)



if __name__ == '__main__':
    main()
