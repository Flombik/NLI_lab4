import nltk
from nltk.corpus import wordnet
import docx
import re
from flask import Flask
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField, TextAreaField
from werkzeug.utils import secure_filename

grammar = """
       P: {<IN>}
       PV: {<V.*|MD>}
       MM: {<DT|PR.*|JJ|NN.*>+}    
       PP: {<IN><MM>}               
       PV: {<V.*><MM|RB|PP|LINK>+$} 
       LINK: {<MM><PV>}           
       """
cp = nltk.RegexpParser(grammar)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a really really really really long secret key'


class AnalysisForm(FlaskForm):
    text = TextAreaField("Текст: ")
    file = FileField('Анализ файла')
    submit = SubmitField("Анализ")


@app.route('/analysis/', methods=['get', 'post'])
def analysis():
    form = AnalysisForm()
    if form.validate_on_submit():
        if form.text.data:
            text = form.text.data
        if form.file.data:
            filename = secure_filename(form.file.data.filename)
            form.file.data.save('uploads/' + filename)
            doc = docx.Document('uploads/' + filename)
            text = ''
            for paragraph in doc.paragraphs:
                text = ' '.join([text, paragraph.text])
        text = text.replace('\n', ' ')
        text = text.replace('–', ' ')
        word_list = re.sub("[.,?!'\";:-]+", "", text).lower().split()
        words = dict.fromkeys(word_list)
        to_pop = []
        for word in words:
            if word != '':
                synonyms = []
                antonyms = []
                hyponyms = []
                hyperonyms = []
                syn = wordnet.synsets(word)
                if not syn:
                    to_pop.append(word)
                    continue
                examples = syn[0].examples()
                definition = syn[0].definition()
                for l in syn[0].lemmas():
                    if word != l.name():
                        synonyms.append(l.name())
                    if l.antonyms():
                        antonyms.append(l.antonyms()[0].name())
                for i in syn[0].hyponyms():
                    hyponyms.append(i.lemma_names()[0])
                for j in syn[0].hypernyms():
                    hyperonyms.append(j.lemma_names()[0])
                examp = "examples = [" + \
                    " ".join([str(elem) for elem in examples]) + "]"
                desc = "definition = [" + \
                    "".join([str(elem) for elem in definition]) + "]"
                syn = "synonyms = [" + \
                    " ".join([str(elem) for elem in synonyms]) + "]"
                ant = "antonyms = [" + \
                    " ".join([str(elem) for elem in antonyms]) + "]"
                hypo = "hyponyms = [" + \
                    " ".join([str(elem) for elem in hyponyms]) + "]"
                hype = "hyperonyms = [" + \
                    " ".join([str(elem) for elem in hyperonyms]) + "]"
                result_str = "\n".join([examp, desc, syn, ant, hypo, hype])
                words[word] = result_str
        for word in to_pop:
            words.pop(word)
        return render_template('show_result.html', words=words)
    return render_template('analysis.html', form=form)


@app.route('/help/')
def help():
    return render_template('help.html')


@app.route('/')
def index():
    return redirect(url_for('help'))


if __name__ == '__main__':
    app.run()
