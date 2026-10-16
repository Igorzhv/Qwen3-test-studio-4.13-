import json
import re
from pathlib import Path
import streamlit as st
from engine import ROOT, load_model, generate, validate, demo_question
from quiz_bank import bank_questions, BANK

st.set_page_config(page_title='Qwen Test Studio', page_icon='🎓', layout='wide')
st.markdown('''<style>.block-container{padding-top:1.5rem;max-width:1250px}div[data-testid="stMetric"]{background:#142a43;border:1px solid #49617b;border-radius:12px;padding:12px}h1{letter-spacing:-.8px}</style>''', unsafe_allow_html=True)
st.title('🎓 Qwen Test Studio · Військова освіта')
st.caption('НУОУ · Варіант 5 · Qwen3-0.6B + LoRA · навчальний прототип')

@st.cache_resource(show_spinner=False)
def cached_model(adapter):
    return load_model(adapter)

with st.sidebar:
    st.header('⚙️ Налаштування')
    mode = st.radio('Режим', ['Навчальний банк (демо)', 'Демо за власним текстом', 'Qwen3-0.6B (базова)', 'Qwen3-0.6B + LoRA'])
    count = st.select_slider('Кількість запитань', options=[1,3,5,10,20], value=5)
    st.info('Демо та банк — не генерація ШІ. Qwen/LoRA — окремі експериментальні режими; якість LoRA не підтверджена.')
    st.caption('Не вводьте матеріали з обмеженим доступом чи реальні оперативні відомості.')

t1,t2,t3=st.tabs(['📝 Створення і проходження тесту','📊 Результати LoRA','📚 Про застосунок'])
with t1:
    st.subheader('Створити навчальний тест')
    st.write('Використай готові відкриті військово-освітні питання або введи власний навчальний текст.')
    example='Інформаційно-аналітичне забезпечення підтримує обґрунтоване прийняття управлінських рішень. Достовірність, актуальність і повнота є важливими властивостями даних.'
    user_text=st.text_area('Навчальний текст',value=example,height=120)
    uploaded=st.file_uploader('Або завантаж TXT чи DOCX (лише відкриті матеріали)',type=['txt','docx'])
    if uploaded:
        try:
            if uploaded.name.lower().endswith('.txt'):
                user_text=uploaded.getvalue().decode('utf-8-sig')
            else:
                from docx import Document
                from io import BytesIO
                doc=Document(BytesIO(uploaded.getvalue()))
                user_text='\n'.join(p.text for p in doc.paragraphs if p.text.strip())
            st.success(f'Завантажено текст: {len(user_text)} символів')
            with st.expander('Переглянути завантажений текст'): st.text(user_text[:12000])
        except Exception as exc: st.error(f'Не вдалося прочитати файл: {exc}')
    if st.button('✨ Створити тест',type='primary'):
        questions=[]; errors=[]
        if mode=='Навчальний банк (демо)':
            questions=bank_questions(count)
        elif not user_text.strip():
            st.warning('Введіть або завантажте текст.')
        elif mode=='Демо за власним текстом':
            parts=[x.strip() for x in re.split(r'(?<=[.!?])\s+',user_text) if len(x.strip())>20]
            if not parts: parts=[user_text]
            for i in range(count):
                q=demo_question(parts[i%len(parts)])
                q['source']='Детермінований шаблон (не ШІ)'
                questions.append(q)
            if count>len(parts): st.info('Речення повторюються: для різноманітності додай більше навчального тексту.')
        else:
            try:
                with st.spinner('Генерація Qwen: на CPU може тривати кілька хвилин...'):
                    tok,model=cached_model(mode.endswith('LoRA'))
                    parts=[p.strip() for p in re.split(r'(?<=[.!?])\s+',user_text) if len(p.strip())>25] or [user_text]
                    for i in range(count):
                        raw=generate(tok,model,parts[i%len(parts)])
                        q=validate(raw)
                        if q:
                            q['source']=mode
                            questions.append(q)
                        else: errors.append({'номер':i+1,'raw':raw[:1500]})
            except Exception as exc: st.error(f'Помилка моделі: {exc}')
        st.session_state['quiz']=questions
        st.session_state['errors']=errors
        st.session_state['answers']={}
        st.session_state['graded']=False
    questions=st.session_state.get('quiz',[])
    if questions:
        st.divider()
        st.subheader(f'Тестування · {len(questions)} запитань')
        with st.form('quiz_form'):
            for i,q in enumerate(questions):
                st.markdown(f'**{i+1}. {q["question"]}**')
                st.radio('Оберіть одну відповідь',list('ABC'),format_func=lambda k,q=q:f'{k}. {q["options"][k]}',key=f'quiz_{i}',index=None)
            submitted=st.form_submit_button('✅ Завершити та оцінити',type='primary')
        if submitted:
            answers=[st.session_state.get(f'quiz_{i}') for i in range(len(questions))]
            st.session_state['answers']=answers
            st.session_state['graded']=True
        if st.session_state.get('graded'):
            answers=st.session_state['answers']
            correct=sum(a==q['answer'] for a,q in zip(answers,questions))
            pct=round(100*correct/len(questions))
            c1,c2,c3=st.columns(3)
            c1.metric('Правильних',f'{correct}/{len(questions)}')
            c2.metric('Результат',f'{pct}%')
            c3.metric('Помилок / пропусків',len(questions)-correct)
            st.bar_chart({'Кількість':{'Правильні':correct,'Інші':len(questions)-correct}})
            with st.expander('Розбір відповідей та ключі'):
                for i,(q,a) in enumerate(zip(questions,answers)):
                    st.write(f'{i+1}. {"✅" if a==q["answer"] else "❌"} Ваша: {a or "не вибрано"} · правильна: {q["answer"]} — {q["options"][q["answer"]]}')
        payload=json.dumps(questions,ensure_ascii=False,indent=2)
        st.download_button('⬇️ Завантажити тест JSON',payload,'military_education_quiz.json','application/json')
        st.caption('Походження: '+', '.join(sorted({q.get('source','невідоме') for q in questions})))
    errors=st.session_state.get('errors',[])
    if errors:
        st.warning(f'Некоректних відповідей Qwen: {len(errors)}. Вони не підміняються демонстраційними запитаннями.')
        with st.expander('Переглянути некоректні генерації'): st.json(errors)
with t2:
    before=json.loads((ROOT/'data/before.json').read_text(encoding='utf-8'))
    after=json.loads((ROOT/'data/after.json').read_text(encoding='utf-8'))
    a,b,c=st.columns(3)
    a.metric('Навчальних прикладів',30);b.metric('Контрольних',5);c.metric('Епох LoRA',5)
    st.subheader('Структурно валідні JSON: до / після LoRA')
    st.bar_chart({'Валідні JSON':{'До LoRA':sum(bool(x.get('valid_format')) for x in before),'Після LoRA':sum(bool(x.get('valid_format')) for x in after)}})
    st.warning('Фактично 0/5 до та 0/5 після. Покращення генерації не підтверджено.')
    st.dataframe([{'Тема':b.get('topic',''),'До':'Так' if b.get('valid_format') else 'Ні','Після':'Так' if a.get('valid_format') else 'Ні'} for b,a in zip(before,after)],hide_index=True,use_container_width=True)
    with st.expander('Сирі відповіді'):
        idx=st.selectbox('Контрольний текст',range(len(before)),format_func=lambda i:before[i].get('topic',str(i+1)))
        l,r=st.columns(2)
        l.text_area('До LoRA',before[idx].get('raw',''),height=200)
        r.text_area('Після LoRA',after[idx].get('raw',''),height=200)
with t3:
    st.markdown('''**Архітектура:** навчальний текст → Qwen3-0.6B → необов’язковий LoRA → перевірка JSON → тест. Окремо працює відкритий демонстраційний банк.\n\n**Модель:** [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B). **Експеримент:** 30 синтетичних навчальних прикладів, 5 контрольних, 5 епох.\n\n**Обмеження:** готовий банк — авторські синтетичні питання, не результат ШІ; демонстрація за текстом — шаблон. Qwen може генерувати некоректний JSON або неточні відповіді. Перевіряйте зміст вручну.\n\n**Безпека:** не використовуйте інформацію з обмеженим доступом або реальні оперативні обставини.''')
    st.metric('Питань у відкритому банку',len(BANK))
