import streamlit as st

from src.chat_engine import AcademicChatEngine


st.set_page_config(
    page_title="Ela Academic Assistant",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Ela Academic Assistant")

st.write(
    "Belgeleriniz üzerinde yerel (Foundry Local) çalışan akademik asistan."
)


if "engine" not in st.session_state:
    with st.spinner("Model yükleniyor..."):
        engine = AcademicChatEngine()
        engine.initialize()
        st.session_state.engine = engine


question = st.text_input(
    "Sorunuzu yazın",
    placeholder=(
        "Örneğin: Erasmus davet mektubunda "
        "hangi bilgiler bulunmalıdır?"
    ),
)

if st.button("Sor"):
    if question.strip():
        with st.spinner("Belgeler aranıyor..."):
            result = st.session_state.engine.answer(
                question
            )

        st.subheader("📌 Cevap")
        st.write(result["answer"])

        st.subheader("📚 Kaynaklar")

        for source in result["sources"]:
            st.markdown(
                f"""
**{source['document_name']}**

Kategori: `{source['category']}`

Chunk: `{source['chunk_index']}`

Benzerlik Skoru: `{source['score']}`
"""
            )