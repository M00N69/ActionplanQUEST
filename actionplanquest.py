import streamlit as st
import pandas as pd
from pocketgroq import GroqProvider

# Configuration de la page
st.set_page_config(layout="wide")

# Ajouter les styles CSS personnalisés
st.markdown(
    """
    <style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #004080;
        text-align: center;
        margin-bottom: 25px;
    }
    .dataframe-container {
        margin-bottom: 20px;
    }
    .banner {
        background-image: url('https://github.com/M00N69/BUSCAR/blob/main/logo%2002%20copie.jpg?raw=true');
        background-size: cover;
        height: 200px;
        background-position: center;
        margin-bottom: 20px;
    }
    div.stButton > button {
        background-color: #004080;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #0066cc;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Ajouter la bannière
st.markdown('<div class="banner"></div>', unsafe_allow_html=True)

# Initialiser PocketGroq
def get_groq_provider():
    if not st.session_state.get('api_key'):
        st.error("Veuillez entrer votre clé API Groq.")
        return None
    return GroqProvider(api_key=st.session_state.api_key)

# Fonction pour charger le fichier Excel avec le plan d'action
def load_action_plan(uploaded_file):
    try:
        action_plan_df = pd.read_excel(uploaded_file, header=11)
        action_plan_df = action_plan_df[["requirementNo", "requirementText", "requirementExplanation"]]
        action_plan_df.columns = ["Numéro d'exigence", "Exigence IFS Food 8", "Explication (par l’auditeur/l’évaluateur)"]
        return action_plan_df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
        return None

# Fonction pour générer une recommandation avec Groq et CoT
def generate_ai_recommendation_groq(non_conformity, guide_row, additional_context):
    groq = get_groq_provider()
    if not groq:
        return "Erreur: clé API non fournie."

    general_context = (
        "En tant qu'expert en IFS Food 8 et en technologies alimentaires, pour chaque non-conformité constatée lors d'un audit, veuillez fournir :\n"
        "- une recommandation de correction (action immédiate),\n"
        "- le type de preuve attendu (élément tangible comme photo ou document),\n"
        "- une analyse de la cause probable (identifier l'origine de la non-conformité),\n"
        "- une recommandation d'action corrective (éliminer la cause racine pour prévenir la réapparition).\n"
    )
    prompt = f"""
    {general_context}
    Non-conformité issue d'un audit IFS Food 8 :
    - Exigence : {non_conformity['Numéro d\'exigence']}
    - Description : {non_conformity['Exigence IFS Food 8']}
    - Constat détaillé : {non_conformity['Explication (par l’auditeur/l’évaluateur)']}
    Guide IFSv8 :
    - Bonnes pratiques : {guide_row['Good practice']}
    - Éléments à vérifier : {guide_row['Elements to check']}
    - Questions exemples : {guide_row['Example questions']}
    Contexte supplémentaire :
    - {additional_context}
    Fournissez une recommandation complète en appliquant une réflexion étape par étape.
    """
    try:
        return groq.generate(prompt, max_tokens=1500, temperature=0, use_cot=True)
    except Exception as e:
        st.error(f"Erreur lors de la génération de la recommandation : {str(e)}")
        return None

# Fonction pour récupérer les informations du guide
def get_guide_info(num_exigence, guide_df):
    try:
        guide_row = guide_df[guide_df['NUM_REQ'].str.contains(str(num_exigence), na=False)]
        if guide_row.empty:
            st.error(f"Aucune correspondance trouvée pour l'exigence : {num_exigence}")
            return None
        return guide_row.iloc[0]
    except Exception as e:
        st.error(f"Erreur lors de la recherche dans le guide : {str(e)}")
        return None

# Fonction pour générer des questions dynamiques
def generate_dynamic_questions(guide_row, non_conformity):
    bonnes_pratiques = guide_row.get('Good practice', 'Non spécifié')
    elements_a_verifier = guide_row.get('Elements to check', 'Non spécifié')
    exemple_questions = guide_row.get('Example questions', 'Non spécifié')
    exigence_text = non_conformity['Exigence IFS Food 8']
    
    questions = [
        f"Selon le constat de l'auditeur, quelles pratiques actuelles pourraient être améliorées concernant : {exigence_text} ? (Bonnes pratiques : {bonnes_pratiques})",
        f"Quelles vérifications ou procédures permettent d'assurer la conformité à cette exigence ? (Éléments à vérifier : {elements_a_verifier})",
        f"Quelles mesures supplémentaires pourraient prévenir des risques similaires dans le futur ? (Exemples : {exemple_questions})",
    ]
    return questions

# Fonction principale
def main():
    st.markdown('<div class="main-header">Assistant VisiPilot pour Plan d\'Actions IFS</div>', unsafe_allow_html=True)
    
    with st.expander("Comment utiliser cette application"):
        st.write("""
        **Étapes d'utilisation :**
        1. Téléchargez votre plan d'actions IFSv8.
        2. Sélectionnez une exigence.
        3. Les recommandations seront basées sur une analyse détaillée.
        """)

    if 'recommendation_expanders' not in st.session_state:
        st.session_state['recommendation_expanders'] = {}

    api_key = st.text_input("Entrez votre clé API Groq :", type="password")
    if api_key:
        st.session_state.api_key = api_key

    uploaded_file = st.file_uploader("Téléchargez votre plan d'action (fichier Excel)", type=["xlsx"])
    if uploaded_file:
        action_plan_df = load_action_plan(uploaded_file)
        if action_plan_df is not None:
            guide_df = pd.read_csv("https://raw.githubusercontent.com/M00N69/Action-planGroq/main/Guide%20Checklist_IFS%20Food%20V%208%20-%20CHECKLIST.csv")
            
            st.write("## Plan d'Action IFS")
            for index, row in action_plan_df.iterrows():
                cols = st.columns([1, 4, 4, 2])
                cols[0].write(row["Numéro d'exigence"])
                cols[1].write(row["Exigence IFS Food 8"])
                cols[2].write(row["Explication (par l’auditeur/l’évaluateur)"])
                
                if cols[3].button("Générer Recommandation", key=f"generate_{index}"):
                    guide_row = get_guide_info(row["Numéro d'exigence"], guide_df)
                    if guide_row is not None:
                        questions = generate_dynamic_questions(guide_row, row)
                        with st.form(key=f"form_{index}"):
                            responses = [st.text_input(question) for question in questions]
                            if st.form_submit_button("Soumettre"):
                                additional_context = "\n".join(responses)
                                recommendation_text = generate_ai_recommendation_groq(row, guide_row, additional_context)
                                st.session_state['recommendation_expanders'][index] = recommendation_text
                if index in st.session_state['recommendation_expanders']:
                    st.expander(f"Recommandation pour {row['Numéro d\'exigence']}").markdown(st.session_state['recommendation_expanders'][index])

if __name__ == "__main__":
    main()
