from io import StringIO

from tkinter import *
from tkinter import scrolledtext
import datetime as datetime
import json
import re
import sys

from natasha import (
    Segmenter,
    MorphVocab,

    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,

    PER,
    NamesExtractor,
    DatesExtractor,

    Doc
)


segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)
names_extractor = NamesExtractor(morph_vocab)
dates_extractor = DatesExtractor(morph_vocab)



def raw_to_date(raw_date):
    if raw_date.get('year'):
        year = raw_date.get('year')
    else:
        year = 2022
    if raw_date.get('month'):
        month = raw_date.get('month')
    else:
        month = 1
    if raw_date.get('day'):
        day = raw_date.get('day')
    else:
        day = 1

    return(datetime.date(year, month, day))

def get_dates(text):
  dates = []
  matches = dates_extractor(text)
  date_list = [raw_to_date(date.fact.as_json) for date in matches]
  return date_list

def birthdate(date_list):
    try:
        if min(date_list) < datetime.date(2004, 1, 1):
            return f"дата рождения: {min(date_list)}"
        else:
            return 'дата рождения: не указана'
    except:
        return 'дата рождения: не указана'

def deathdate(date_list):
    try:
        if max(date_list) > datetime.date(2022, 2, 24):
            return(f"дата смерти: {max(date_list)}")
        else:
            return('дата смерти: не указана')
    except:
        return 'дата смерти: не указана'

def find_ranks(doc):
    ranks_dict = json.load(open("ranks_dict.json"))
    ranks = []
    replacements_ranks = [
        ('младш[а-я]+', 'младший'),
        ('старш.[^н]', 'старший'),
        ('\s|-|\n', '')]

    for old, new in replacements_ranks:
        text = re.sub(old, new, doc.text.lower())
    for key in ranks_dict.keys():
        if re.search(key, text):
            ranks.append(ranks_dict[key])
    if len(ranks) > 0:

        return f"звание: {', '.join(list(set(ranks)))}"
    else:
        return "звание не указано"

def find_names(spans):
    names = []
    for span in spans:
        if span.type == PER:
            if len(span.normal.strip().split(' ')) > 1:
                names.append(span.normal)
    return set(names)

def parse_occupation(oc):
    oc = oc.replace("\'", "")
    oc = oc.strip()
    oc = oc.lower()
    return oc

def find_occupations(doc):
    occups = []
    with open("./positions_set.txt", 'r') as file:
        occups = file.readlines()
        occups = [parse_occupation(oc) for oc in occups]

    positions_per = []
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        if token.lemma in occups:
            positions_per.append(token.lemma)

    if len(positions_per) > 0:
        return f"должность: {', '.join(occups)}"
    else:
        return 'должность не указана'

def parse_text(text):
    doc = Doc(text)

    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    doc.tag_ner(ner_tagger)

    for span in doc.spans:
        span.normalize(morph_vocab)

    # get annot text
    my_result = StringIO()
    sys.stdout = my_result
    doc.ner.print()
    annot_text = my_result.getvalue()

    # get dates
    date_list = get_dates(text)

    # get title
    ranks = find_ranks(doc)

    # get names
    names = find_names(doc.spans)

    # get occupations
    occups = find_occupations(doc)


    return annot_text, birthdate(date_list), deathdate(date_list), ranks, f"имя: {', '.join(names)}", occups

def initialize_gui():
    window = Tk()
    window.title("Attribute extractor")
    window.geometry('700x1000')

    # first label
    lbl = Label(window, text="Текст поста:", font=("Arial Bold", 30), padx=5, pady=5)
    lbl.grid(column=30, row=10)

    # text window
    # txt = Entry(window)
    txt = scrolledtext.ScrolledText(window)
    txt.place(x=30,
              y=70,
              width=600,
              height=300)

    # output label
    lbl_out = Label(window, text="output:", font=("Arial", 14), padx=5, pady=5, anchor=W, justify=LEFT)
    lbl_out.place(x=30,
                  y=450,
                  width=600,
                  height=300)

    # parse text button
    def clicked():
        text = txt.get("1.0", 'end-1c')
        annot_text, birth_msg, death_msg, titles_msg, names_msg, occups_msg = parse_text(text)
        txt.delete(1.0, END)
        txt.insert(INSERT, annot_text)

        # update the description:
        summary = names_msg + "\n" + titles_msg + "\n" + occups_msg + "\n" + birth_msg + "\n" + death_msg
        lbl_out.configure(text=summary)


    btn = Button(window, text="парсим!", command=clicked)
    btn.place(x=30,
              y=400,
              width=150,
              height=20)

    window.mainloop()


#############################################

if __name__ == "__main__":

    initialize_gui()

