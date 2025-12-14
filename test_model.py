import pandas as pd
from transformers import pipeline

# 1. incarcare model
print("Se incarca modelul...")
classifier = pipeline("text-classification", model="dima806/email-spam-detection-distilbert")
#alte task-uri ca parametri ar fi "summarization","translation"
#in classifier e practic stocat modelul

# 2. incarcare fisier .csv de test
nume_fisier = "spam_Emails_data.csv"
try:
    df = pd.read_csv(nume_fisier)
    print(f"S-a încărcat fișierul cu {len(df)} email-uri.")#functia len() returneaza numarul de randuri
except FileNotFoundError:
    print(f"EROARE: Nu gasesc fișierul '{nume_fisier}'.")
    exit()

# 3. input dat de utilizator
try:
    n = int(input("\nCate email-uri random se duc spre testare? (ex: 50): "))
except ValueError:
    print("Numar invalid.")
    exit()

dataset_random = df.sample(n)

print(f"\n INCEPE TESTAREA PE {n} EMAIL-URI: \n")

scor_corecte = 0

for index, row in dataset_random.iterrows(): #iterrows() e functie din libraria panda si parcurge rand cu rand dataset-ul
    text_email = str(row['text'])
    eticheta_reala = str(row['label']).strip().lower()#strip() sterge spatiile si lower() face conversie la litere mici


    rezultat = classifier(text_email, truncation=True, max_length=512)#modelul ales poate citi maxim 512 token-uri
    #functia returneaza un vector cu elemente de tip [{'label': 'Spam', 'score': 0.998},{'label': 'Spam', 'score': 0.98},etc]
    eticheta_ai_raw = rezultat[0]['label']
    prediction_score = rezultat[0]['score']
    raw_lower = eticheta_ai_raw.lower()

    if raw_lower in ['spam', 'label_1']:
        eticheta_ai_final = 'spam'
    elif raw_lower in ['ham', 'label_0', 'no spam']:
        eticheta_ai_final = 'ham'
    else:
        eticheta_ai_final = raw_lower


    if eticheta_ai_final == eticheta_reala:
        scor_corecte += 1
    else:
        print(f"GRESIT la randul {index}:")
        print(f"   CSV: '{eticheta_reala}' | AI: '{eticheta_ai_raw}'")
        print(f"   AI_score: {prediction_score:.4f}")
        print("-" * 30)

# raport final
print(f"\nREZULTAT FINAL: {scor_corecte} din {n}")
print(f"Acuratete: {(scor_corecte / n) * 100:.2f}%")