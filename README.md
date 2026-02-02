# NoirBudget (Finance Advisor Budgeting Tool - ITA)

NoirBudget è una dashboard desktop in **Python + Tkinter (ttk)** con **tema nero** per la gestione delle finanze domestiche: conti bancari, carte di credito, spese previste (es. addebiti SDD), stipendio e salvataggio persistente su file JSON.

> File principale: `finance_advisor_budgeting_tool_ITA.py`  
> Dati salvati in locale: `noirbudget_data.json`

---

## ✨ Funzionalità

### ✅ Conti bancari
- Aggiungi **banche/conti** con **saldo lordo**
- Per ogni conto puoi inserire **spese previste** (es. SDD/abbonamenti/utenze)
- Il sistema calcola automaticamente:
  - **Spese previste totali**
  - **Saldo effettivo** = saldo lordo − spese previste

### ✅ Carte di credito
- Aggiungi carte con **saldo da pagare**
- Sezione spese fisse della carta (solo elenco, non dedotte dal saldo conto)

### ✅ Categorie dinamiche
- Categorie base: **Abbonamenti ricorrenti**, **Palestra**
- Puoi **creare nuove categorie** direttamente dall’interfaccia:
  - scrivi “Nuova categoria”
  - premi “Aggiungi categoria”
  - la categoria diventa disponibile nei menu a tendina

### ✅ Stipendio
- Inserisci importo stipendio
- Seleziona su quale **conto** viene accreditato (informativo per dashboard)

### ✅ Dashboard
Mostra:
- Liquidità (conti **al netto** delle spese previste)
- Debiti carte
- Netto
- Spese previste totali sui conti
- Stipendio
- **Data e ora dell’ultimo salvataggio**

### ✅ Salvataggio e ripristino
- Salvataggio su file JSON (`noirbudget_data.json`)
- Ripristino automatico all’avvio
- Bottone “💾 Salva ora”
- Salvataggio anche alla chiusura della finestra

---

## 📦 Requisiti

- **Python 3.10+** consigliato (funziona anche con 3.9 nella maggior parte dei casi)
- Tkinter incluso di solito nelle installazioni standard di Python su Windows/macOS  
  (su alcune distro Linux potrebbe richiedere pacchetti aggiuntivi)
  RACCOMANDATO IL LAUNCHER PYTHON LAUNCHER PRO: https://github.com/mikeminer/Python-Launcher-PRO

python finance_advisor_budgeting_tool_ITA.py
