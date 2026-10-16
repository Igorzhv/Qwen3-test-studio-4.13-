# Qwen Test Studio — варіант 5 НУОУ

Навчальний вебзастосунок Streamlit: генератор одного запитання з трьома відповідями та ключем. Є **демонстраційний шаблонний режим**, **базова Qwen3-0.6B** і **Qwen3-0.6B + реальний LoRA-адаптер першого експерименту**.

## Windows / VS Code

1. Розпакуйте архів у папку (наприклад `Desktop\Qwen3_Test_Studio`).
2. Відкрийте цю папку у Visual Studio Code: **File → Open Folder**.
3. Встановіть Python 3.11 та розширення Python у VS Code.
4. Двічі натисніть `start_windows.bat` у Провіднику Windows або виконайте у терміналі VS Code:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Якщо PowerShell забороняє активацію, запустіть `.venv\Scripts\python.exe -m streamlit run app.py` (після встановлення залежностей через `.venv\Scripts\python.exe -m pip install -r requirements.txt`).

5. Відкрийте адресу `http://localhost:8501`. Перший запуск режиму Qwen завантажить модель з Hugging Face (потрібен інтернет та вільна RAM). Демонстраційний режим не потребує завантаження моделі.

## Фактичні результати

- Навчальний набір: 30 синтетичних прикладів; контрольний: 5.
- LoRA у Google Colab GPU T4: 5 епох, 40 кроків (за наданими матеріалами).
- Валідність JSON: **0/5 до** і **0/5 після**. Покращення якості не доведено.
- `adapter/` містить справжні ваги першого експерименту, а не покращений повторно навчений адаптер.
- Демонстраційний режим використовує **шаблонне правило**, не ШІ. Він призначений для показу інтерфейсу, а не підтвердження генеративної якості.

## GitHub

Створіть порожній репозиторій на github.com (без README). У терміналі VS Code у папці проєкту виконайте:

```bash
git init
git add .
git commit -m "Add Qwen Test Studio demo and LoRA experiment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/qwen-test-studio.git
git push -u origin main
```

Замініть `YOUR_USERNAME` на власний логін. GitHub може вимагати авторизацію у браузері. Не завантажуйте секрети або дані з обмеженим доступом.

## Структура

- `app.py` — вебінтерфейс і результати експерименту
- `engine.py` — Qwen/LoRA, генерація та JSON-валідатор
- `data/train.json`, `data/test.json` — синтетичні навчальні та контрольні приклади
- `data/before.json`, `data/after.json` — фактичні результати
- `adapter/` — ваги першого LoRA-експерименту
- `start_windows.bat` — запуск у Windows

Джерело моделі: https://huggingface.co/Qwen/Qwen3-0.6B
