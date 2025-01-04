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
    /* Style pour l'expander */
    .st-emotion-cache-1h9usn1 {
        background-color: #e0f7fa !important; /* Fond bleu clair pour l'expander */
        border: 1px solid #004080 !important; /* Bordure bleu foncé */
        border-radius: 5px;
    }
    /* Style pour le formulaire */
    .stForm {
        background-color: #f0f8ff; /* Fond clair pour le formulaire */
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
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

# Charger le fichier Excel avec le plan d'action
def load_action_plan(uploaded_file):
    try:
        action_plan_df = pd.read_excel(uploaded_file, header=11)
        action_plan_df = action_plan_df[["requirementNo", "requirementText", "requirementExplanation"]]
        action_plan_df.columns = ["Numéro d'exigence", "Exigence IFS Food 8", "Explication (par l’auditeur/l’évaluateur)"]
        return action_plan_df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier: {str(e)}")
        return None

# Récupérer les informations du guide
def get_guide_info(num_exigence, guide_df):
    try:
        guide_row = guide_df[guide_df['NUM_REQ'].str.contains(str(num_exigence), na=False)]
        if guide_row.empty:
            st.error(f"Aucune correspondance trouvée pour le numéro d'exigence : {num_exigence}")
            return None
        return guide_row.iloc[0]
    except Exception as e:
        st.error(f"Erreur lors de la recherche dans le guide : {str(e)}")
        return None

# Générer des questions dynamiques pour l'analyse des causes
def generate_dynamic_questions(guide_row, non_conformity):
    bonnes_pratiques = guide_row.get('Good practice', 'Non spécifié')
    elements_a_verifier = guide_row.get('Elements to check', 'Non spécifié')
    exemple_questions = guide_row.get('Example questions', 'Non spécifié')
    exigence_text = non_conformity['Exigence IFS Food 8']
    audit_comment = non_conformity['Explication (par l’auditeur/l’évaluateur)']
    
    questions = [
        f"Quelles sont les causes potentielles de cette non-conformité ? (Contexte : {audit_comment})",
        f"Quelles sont les procédures actuelles pour répondre à cette exigence ? (Éléments à vérifier : {elements_a_verifier})",
        f"Quelles mesures supplémentaires pourraient prévenir des risques similaires dans le futur ? (Exemples : {exemple_questions})",
    ]
    return questions

# Générer une recommandation avec Groq et CoT
def generate_ai_recommendation_groq(non_conformity, guide_row, additional_context):
    groq = get_groq_provider()
    if not groq:
        return "Erreur: clé API non fournie."

    # Prompt détaillé et explicite avec approche CoT
    prompt = f"""
    En tant qu'expert en IFS Food 8 et en technologies alimentaires, pour chaque non-conformité constatée lors d'un audit, veuillez fournir :
    - une recommandation de correction : action immédiate visant à éliminer la non-conformité détectée en s'assurant qu'elle est adaptée au domaine d'activités du site industriel.
    - le type de preuve attendu : élément tangible (photo, document,...) démontrant la mise en place de la correction.
    - l'analyse de la cause probable : investigation approfondie pour identifier l'origine de la non-conformité en t'assurant que l'analyse est cohérente avec l'acvité du site  (industrie alimentaire).
    - une recommandation d'action corrective : mesure à prendre pour éliminer la cause racine et prévenir la réapparition de la non-conformité.

    Points importants à prendre en compte :
    - Distinction correction / action corrective : La correction est une action immédiate pour rectifier une situation, tandis que l'action corrective vise à éliminer la cause racine et à empêcher la récurrence.
    - Pertinence et exhaustivité : Les recommandations de correction et d'action corrective doivent être adaptées à la non-conformité et traiter tous les aspects du problème.

    Voici une non-conformité issue d'un audit IFS Food 8 :
    - Exigence : {non_conformity['Numéro d\'exigence']}
    - Description : {non_conformity['Exigence IFS Food 8']}
    - Constat détaillé : {non_conformity['Explication (par l’auditeur/l’évaluateur)']}

    Basé sur le guide IFSv8 pour cette exigence :
    - Bonnes pratiques : {guide_row['Good practice']}
    - Éléments à vérifier : {guide_row['Elements to check']}
    - Questions exemples : {guide_row['Example questions']}

    Informations supplémentaires fournies par l'utilisateur :
    - {additional_context}

    Veuillez fournir une recommandation complète avec analyse détaillée en appliquant une approche "Chain of Thought" (réflexion étape par étape).
    """
    try:
        return groq.generate(prompt, max_tokens=1500, temperature=0, use_cot=True)
    except Exception as e:
        st.error(f"Erreur lors de la génération de la recommandation : {str(e)}")
        return None

# Fonction principale
def main():
    st.markdown('<div class="main-header">Assistant VisiPilot pour Plan d\'Actions IFS</div>', unsafe_allow_html=True)

    # Initialiser les états de session
    if 'recommendation_expanders' not in st.session_state:
        st.session_state['recommendation_expanders'] = {}
    if 'responses' not in st.session_state:
        st.session_state['responses'] = {}
    if 'show_popup' not in st.session_state:
        st.session_state['show_popup'] = {}
    if 'current_index' not in st.session_state:
        st.session_state['current_index'] = None

    # Clé API Groq
    api_key = st.text_input("Entrez votre clé API Groq :", type="password")
    if api_key:
        st.session_state.api_key = api_key

    # Télécharger le fichier Excel
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
                
                # Bouton pour générer les recommandations
                if cols[3].button("Générer Recommandation", key=f"generate_{index}"):
                    st.session_state['current_index'] = index
                    st.session_state['show_popup'][index] = True

                # Afficher le popup si nécessaire
                if st.session_state.get('show_popup', {}).get(index, False):
                    guide_row = get_guide_info(row["Numéro d'exigence"], guide_df)
                    if guide_row is not None:
                        questions = generate_dynamic_questions(guide_row, row)
                        with st.form(key=f"form_{index}"):
                            st.write("Veuillez répondre aux questions suivantes pour fournir plus de contexte :")
                            responses = [st.text_input(question) for question in questions]
                            if st.form_submit_button("Soumettre"):
                                additional_context = "\n".join(responses)
                                recommendation_text = generate_ai_recommendation_groq(row, guide_row, additional_context)
                                st.session_state['recommendation_expanders'][index] = recommendation_text
                                st.session_state['show_popup'][index] = False
                                st.session_state['responses'][index] = responses

                # Afficher la recommandation si elle existe
                if index in st.session_state['recommendation_expanders']:
                    expander = st.expander(f"Recommandation pour {row['Numéro d\'exigence']}", expanded=True)
                    expander.markdown(st.session_state['recommendation_expanders'][index])

                # Afficher les réponses si elles existent
                if index in st.session_state['responses']:
                    st.write("Réponses fournies :")
                    for i, response in enumerate(st.session_state['responses'][index]):
                        st.write(f"Question {i+1}: {response}")

if __name__ == "__main__":
    main()
