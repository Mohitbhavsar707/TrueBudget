# TrueBudget

TrueBudget is a local, AI-assisted personal budgeting dashboard.  
It helps users understand their finances, generate a monthly spending plan, and receive budgeting advice using only free, local tools.

The application runs entirely on the user’s machine and does not require any paid APIs or cloud services.

---

## What TrueBudget Does

TrueBudget allows users to:

- Enter income sources and fixed expenses  
- Set savings goals (amount or percent)  
- Allocate a discretionary budget automatically  
- View budget health metrics and charts  
- Test different savings scenarios  
- Receive AI-generated budgeting advice using a local language model  

All calculations are done using deterministic budgeting logic, and the AI is used only to explain and summarize results.

---

## Built With

- Python  
- Streamlit (UI)  
- SQLite (database)  
- Plotly (charts)  
- Ollama (local LLM)  

No external APIs or cloud services are required.

---

## How to Run the Project

### 1. Clone the repository
git clone https://github.com/YOURUSERNAME/TrueBudget.git
cd TrueBudget

### 2. Clone the repository
Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Install Ollama and a model
brew install --cask ollama
ollama pull llama3.1:8b

### 5. Run the app
streamlit run app/main.py
