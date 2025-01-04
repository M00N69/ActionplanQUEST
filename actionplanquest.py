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
        st.error(f"Erreur lors de la lecture du fichier: {str(e)}")
        return None

# Fonction pour générer des questions dynamiques adaptées en français
def generate_dynamic_questions(guide_row, non_conformity):
    bonnes_pratiques = guide_row.get('Good practice', 'Non spécifié')
    elements_a_verifier = guide_row.get('Elements to check', 'Non spécifié')
    exemple_questions = guide_row.get('Example questions', 'Non spécifié')
    
    exigence_text = non_conformity['Exigence IFS Food 8']
    audit_comment = non_conformity['Explication (par l’auditeur/l’évaluateur)']
    
    questions = []
    
    # Question 1 : Sur les pratiques actuelles
    questions.append(
        f"Selon le commentaire de l'auditeur, des améliorations sont nécessaires concernant : '{exigence_text}'. "
        f"Quelles sont les pratiques actuelles sur le site pour répondre à cette exigence ? "
        f"(Bonnes pratiques à suivre : {bonnes_pratiques})"
    )
    
    # Question 2 : Sur les contrôles et procédures
    questions.append(
        f"Quelles vérifications ou procédures spécifiques sont actuellement mises en place pour cette exigence ? "
        f"Ces procédures permettent-elles de couvrir tous les cas identifiés dans les constats de l'auditeur ? "
        f"(Points à vérifier selon le guide : {elements_a_verifier})"
    )
    
    # Question 3 : Sur les mesures correctives
    questions.append(
        f"Quelles mesures spécifiques pourraient être mises en œuvre pour prévenir les risques identifiés dans le constat de l'auditeur ? "
        f"Comment ces mesures peuvent-elles être adaptées aux produits concernés ? "
        f"(Exemple d'analyse selon le guide : {exemple_questions})"
    )
    
    return questions

# Fonction principale
def main():
    st.markdown(
        """
        <div class="main-header">Assistant VisiPilot pour Plan d'Actions IFS</div>
        """, 
        unsafe_allow_html=True
    )
    
    with st.expander("Comment utiliser cette application"):
        st.write("""
        **Étapes d'utilisation:**
        1. Téléchargez votre plan d'actions IFSv8.
        2. Sélectionnez un numéro d'exigence.
        3. Les recommandations générées seront basées sur une analyse détaillée de chaque non-conformité.
        """)

    if 'recommendation_expanders' not in st.session_state:
        st.session_state['recommendation_expanders'] = {}
    if 'show_popup' not in st.session_state:
        st.session_state['show_popup'] = False
    if 'additional_context' not in st.session_state:
        st.session_state['additional_context'] = ""
    if 'current_index' not in st.session_state:
        st.session_state['current_index'] = None

    api_key = st.text_input("Entrez votre clé API Groq:", type="password")
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
                    st.session_state['current_index'] = index
                    st.session_state['show_popup'] = True
                    st.session_state['additional_context'] = ""

                if st.session_state['show_popup'] and st.session_state['current_index'] == index:
                    guide_row = get_guide_info(row["Numéro d'exigence"], guide_df)
                    if guide_row is not None:
                        questions = generate_dynamic_questions(guide_row, row)
                        
                        with st.form(key=f'additional_info_form_{index}'):
                            st.write("Veuillez répondre aux questions suivantes pour fournir plus de contexte :")
                            responses = []
                            for question in questions:
                                responses.append(st.text_input(question))
                            submit_button = st.form_submit_button("Soumettre")

                            if submit_button:
                                additional_context = "\n".join([f"Réponse {i+1}: {resp}" for i, resp in enumerate(responses) if resp])
                                st.session_state['additional_context'] = additional_context
                                st.session_state['show_popup'] = False

                                recommendation_text = generate_ai_recommendation_groq(row, guide_row, additional_context)
                                if recommendation_text:
                                    st.success("Recommandation générée avec succès!")
                                    st.session_state['recommendation_expanders'][index] = {'text': recommendation_text}

                if index in st.session_state['recommendation_expanders']:
                    expander = st.expander(f"Recommandation pour Numéro d'exigence: {row['Numéro d\'exigence']}", expanded=True)
                    expander.markdown(st.session_state['recommendation_expanders'][index]['text'])

if __name__ == "__main__":
    main()
