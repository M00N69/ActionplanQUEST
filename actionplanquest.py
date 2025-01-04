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
    /* Styles pour la bannière */
    .banner {
        background-image: url('https://github.com/M00N69/BUSCAR/blob/main/logo%2002%20copie.jpg?raw=true');
        background-size: cover;
        height: 200px;
        background-position: center;
        margin-bottom: 20px;
    }
    /* Styles personnalisés pour l'expander */
    .st-emotion-cache-1h9usn1 {
        background-color: #e0f7fa !important; /* Fond bleu clair pour l'expander */
        border: 1px solid #004080 !important; /* Bordure bleu foncé */
        border-radius: 5px;
    }
    .st-emotion-cache-p5msec {
        color: #004080 !important; /* Couleur du texte de l'expander */
    }
    /* Styles personnalisés pour les boutons */
    div.stButton > button {
        background-color: #004080; /* Couleur de fond */
        color: white;
        border-radius: 5px;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #0066cc; /* Couleur de fond au survol */
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

# Fonction pour générer une recommandation avec Groq et CoT
def generate_ai_recommendation_groq(non_conformity, guide_row, additional_context):
    groq = get_groq_provider()
    if not groq:
        return "Erreur: clé API non fournie."

    # Instructions affinées et détaillées
    general_context = (
        "En tant qu'expert en IFS Food 8 et en technologies alimentaires, pour chaque non-conformité constatée lors d'un audit, veuillez fournir :\n"
        "- une recommandation de correction : action immédiate visant à éliminer la non-conformité détectée en s'assurant qu'elle est adaptée au domaine d'activités du site industriel.\n"
        "- le type de preuve attendu : élément tangible (photo, document,...) démontrant la mise en place de la correction.\n"
        "- l'analyse de la cause probable : investigation approfondie pour identifier l'origine de la non-conformité en t'assurant que l'analyse est cohérente avec l'acvité du site  (industrie alimentaire).\n"
        "- une recommandation d'action corrective : mesure à prendre pour éliminer la cause racine et prévenir la réapparition de la non-conformité.\n\n"
        "Points importants à prendre en compte :\n"
        "- Distinction correction / action corrective : La correction est une action immédiate pour rectifier une situation, tandis que l'action corrective vise à éliminer la cause racine et à empêcher la récurrence.\n"
        "- Pertinence et exhaustivité : Les recommandations de correction et d'action corrective doivent être adaptées à la non-conformité et traiter tous les aspects du problème.\n"
    )
    
    # Prompt détaillé et explicite
    prompt = f"""
    {general_context}
    Voici une non-conformité issue d'un audit IFS Food 8 :
    - Exigence : {non_conformity['Numéro d\'exigence']}
    - Description : {non_conformity['Exigence IFS Food 8']}
    - Constat détaillé : {non_conformity['Explication (par l’auditeur/l’évaluateur)']}
    
    Basé sur le guide IFSv8 pour cette exigence :
    - Bonnes pratiques : {guide_row['Good practice']}
    - Éléments à vérifier : {guide_row['Elements to check']}
    - Exemple de question à poser : {guide_row['Example questions']}
    
    Informations supplémentaires fournies par l'utilisateur :
    - {additional_context}
    
    Veuillez fournir une recommandation complète avec analyse détaillée en appliquant une approche "Chain of Thought" (réflexion étape par étape).
    """

    try:
        # Analyse toujours avec CoT activé
        return groq.generate(prompt, max_tokens=1500, temperature=0, use_cot=True)
    except Exception as e:
        st.error(f"Erreur lors de la génération de la recommandation : {str(e)}")
        return None

# Fonction pour récupérer les informations du guide en fonction du numéro d'exigence
def get_guide_info(num_exigence, guide_df):
    guide_row = guide_df[guide_df['NUM_REQ'].str.contains(num_exigence, na=False)]
    if guide_row.empty:
        st.error(f"Aucune correspondance trouvée pour le numéro d'exigence : {num_exigence}")
        return None
    return guide_row.iloc[0]

# Fonction pour générer des questions dynamiques basées sur le guide, l'exigence et les commentaires de l'auditeur
def generate_dynamic_questions(guide_row, non_conformity):
    # Extraire les informations du guide
    good_practice = guide_row['Good practice']
    elements_to_check = guide_row['Elements to check']
    example_questions = guide_row['Example questions']
    
    # Extraire les informations de l'exigence et du commentaire de l'auditeur
    exigence_text = non_conformity['Exigence IFS Food 8']
    audit_comment = non_conformity['Explication (par l’auditeur/l’évaluateur)']
    
    # Générer des questions techniques et spécifiques en français
    questions = [
        f"Quel est le type de produit concerné et comment cela influence-t-il les procédures de nettoyage et de désinfection ? (Orientation: {good_practice})",
        f"Quelles sont les procédures actuelles pour nettoyer et désinfecter la machine concernée ? (Orientation: {elements_to_check})",
        f"Quelles mesures supplémentaires pourriez-vous mettre en place pour garantir que la machine soit correctement nettoyée et désinfectée ? (Orientation: {example_questions})"
    ]
    
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
    
    # Initialiser les états de session
    if 'recommendation_expanders' not in st.session_state:
        st.session_state['recommendation_expanders'] = {}
    if 'show_popup' not in st.session_state:
        st.session_state['show_popup'] = False
    if 'additional_context' not in st.session_state:
        st.session_state['additional_context'] = ""
    if 'current_index' not in st.session_state:
        st.session_state['current_index'] = None

    # Clé API Groq
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
                
                # Bouton pour générer les recommandations
                if cols[3].button("Générer Recommandation", key=f"generate_{index}"):
                    st.session_state['current_index'] = index
                    st.session_state['show_popup'] = True
                    st.session_state['additional_context'] = ""  # Réinitialiser les réponses

                # Afficher le popup si nécessaire
                if st.session_state['show_popup'] and st.session_state['current_index'] == index:
                    guide_row = get_guide_info(row["Numéro d'exigence"], guide_df)
                    if guide_row is not None:
                        # Générer des questions dynamiques basées sur le guide, l'exigence et les commentaires de l'auditeur
                        questions = generate_dynamic_questions(guide_row, row)
                        
                        # Utiliser une clé unique pour chaque formulaire
                        with st.form(key=f'additional_info_form_{index}'):
                            st.write("Veuillez répondre aux questions suivantes pour fournir plus de contexte :")
                            q1 = st.text_input(questions[0])
                            q2 = st.text_input(questions[1])
                            q3 = st.text_input(questions[2])
                            submit_button = st.form_submit_button("Soumettre")

                            if submit_button:
                                additional_context = f"Type de produit: {q1}\nProcédures actuelles: {q2}\nMesures supplémentaires: {q3}"
                                st.session_state['additional_context'] = additional_context
                                st.session_state['show_popup'] = False

                                recommendation_text = generate_ai_recommendation_groq(row, guide_row, additional_context)
                                if recommendation_text:
                                    st.success("Recommandation générée avec succès!")
                                    st.session_state['recommendation_expanders'][index] = {'text': recommendation_text}

                # Afficher la recommandation si elle existe
                if index in st.session_state['recommendation_expanders']:
                    expander = st.expander(f"Recommandation pour Numéro d'exigence: {row['Numéro d\'exigence']}", expanded=True)
                    expander.markdown(st.session_state['recommendation_expanders'][index]['text'])

if __name__ == "__main__":
    main()
