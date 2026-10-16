import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL='Qwen/Qwen3-0.6B'
SYSTEM=('Ти створюєш українськомовні навчальні тести. За навчальним текстом сформуй одне запитання, '
        'три різні відповіді A, B, C та правильний ключ. Поверни лише JSON з полями question, options, answer. '
        'options має бути об’єктом з ключами A, B, C. Правильна відповідь має випливати з тексту.')
def validate(raw):
    try:
        raw=re.sub(r'^```(?:json)?\s*|\s*```$', '',raw.strip(),flags=re.I)
        obj=json.loads(raw)
        if not isinstance(obj,dict) or not {'question','options','answer'}<=set(obj):return None
        opts=obj['options']
        if isinstance(opts,list) and len(opts)==3:opts=dict(zip('ABC',opts))
        if not isinstance(opts,dict) or set(opts)!=set('ABC'):return None
        if not isinstance(obj['question'],str) or not obj['question'].strip():return None
        if any(not isinstance(x,str) or not x.strip() for x in opts.values()):return None
        if len({x.strip().casefold() for x in opts.values()})!=3:return None
        if obj['answer'] not in 'ABC' or len(obj['answer'])!=1:return None
        return {'question':obj['question'],'options':opts,'answer':obj['answer']}
    except (ValueError,TypeError,KeyError):return None

def load_model(use_adapter=False):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tokenizer=AutoTokenizer.from_pretrained(MODEL)
    kw={'torch_dtype':torch.float16 if torch.cuda.is_available() else torch.float32}
    model=AutoModelForCausalLM.from_pretrained(MODEL,**kw)
    if use_adapter:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,str(ROOT/'adapter'))
    if torch.cuda.is_available():model=model.to('cuda')
    model.eval()
    return tokenizer,model

def generate(tokenizer,model,text):
    import torch
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':f'Навчальний текст:\n{text}\nСтвори тест у JSON.'}]
    inputs=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors='pt').to(model.device)
    with torch.inference_mode():
        result=model.generate(inputs,max_new_tokens=256,do_sample=False,pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(result[0,inputs.shape[1]:],skip_special_tokens=True).strip()

def demo_question(text):
    """Explicitly labeled deterministic UI demonstration, NOT an LLM result."""
    clean=' '.join(text.split())
    sentences=[x.strip(' .!?') for x in re.split(r'[.!?]+',clean) if len(x.strip())>15]
    statement=(sentences[0] if sentences else clean[:180]).strip()
    if not statement:raise ValueError('Введіть навчальний текст')
    return {'question':'Яке твердження відповідає наведеному навчальному тексту?',
            'options':{'A':statement+'.','B':'У тексті стверджується протилежне наведеному твердженню.',
                       'C':'У тексті відсутня будь-яка інформація за цією темою.'},'answer':'A'}
