# Streamlit + OpenAI 간단 LLM QA 웹앱
import streamlit as st
from openai import OpenAI
from typing import Optional

st.set_page_config(page_title="LLM QA", layout="centered")

st.title("LLM 질의 응답 앱")
st.caption("OpenAI API Key를 입력 후 질문을 보내면 LLM 응답을 반환합니다.")

# API Key를 session_state에 저장해서 다른 페이지로 이동 후 돌아와도 유지되도록 함
if "openai_api_key" not in st.session_state:
	st.session_state.openai_api_key = ""

key_input = st.text_input("OpenAI API Key", type="password", value=st.session_state.openai_api_key)
st.session_state.openai_api_key = key_input


@st.cache_data
def ask_llm(question: str, api_key: str) -> str:
	"""질문과 API Key가 같다면 캐시된 결과를 반환합니다."""
	if not question:
		return ""
	if not api_key:
		return "API Key가 필요합니다. 상단에 입력하세요."

	try:
		client = OpenAI(api_key=api_key)
		resp = client.chat.completions.create(
			model="gpt-3.5-turbo",
			messages=[{"role": "user", "content": question}],
			max_tokens=512,
			temperature=0.2,
		)
		# new library keeps similar structure for chat completion responses
		return resp.choices[0].message.content.strip()
	except Exception as e:
		return f"오류 발생: {e}"


st.markdown("---")

with st.form("qa_form"):
	question = st.text_area("질문을 입력하세요", height=140)
	submitted = st.form_submit_button("질문 보내기")

if submitted:
	if not st.session_state.openai_api_key:
		st.error("OpenAI API Key를 입력하세요.")
	elif not question:
		st.warning("질문을 입력하세요.")
	else:
		with st.spinner("LLM 응답을 가져오는 중..."):
			answer = ask_llm(question, st.session_state.openai_api_key)
		st.subheader("응답")
		st.write(answer)

st.markdown("---")
st.info("한번 실행된 동일한 질문과 API Key 조합은 @st.cache_data로 캐시됩니다.")

