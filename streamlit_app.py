# Streamlit + OpenAI 간단 LLM QA 웹앱
import streamlit as st
from openai import OpenAI
from typing import Optional

st.set_page_config(page_title="LLM QA", layout="centered")

st.title("LLM 질의 응답 앱")
st.caption("OpenAI API Key를 입력 후 질문을 보내면 LLM 응답을 반환합니다.")

# 페이지 선택: QA 또는 Chat
page = st.sidebar.radio("페이지 선택", ["QA", "Chat"]) 

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


if page == "QA":
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

elif page == "Chat":
	st.markdown("---")
	st.header("Chatbot (Responses API)")

	# initialize chat history
	if "chat_history" not in st.session_state:
		st.session_state.chat_history = []  # list of {role: 'user'|'assistant', 'content': str}

	# Clear button
	col1, col2 = st.columns([1, 3])
	with col1:
		if st.button("Clear"):
			st.session_state.chat_history = []
			# Clear the input field as well; Streamlit will rerun automatically on state change
			st.session_state.chat_input = ""
	with col2:
		st.write("대화를 초기화하려면 Clear를 누르세요.")

	# input area
	user_input = st.text_input("메시지를 입력하세요", key="chat_input")
	send = st.button("Send")

	def extract_text_from_response(resp) -> str:
		# try several common shapes from the Responses API
		try:
			if hasattr(resp, "output_text") and resp.output_text:
				return resp.output_text
		except Exception:
			pass
		try:
			# resp.output is often a list of items with content
			out = resp.output
			if out and isinstance(out, list):
				parts = []
				for item in out:
					if isinstance(item, dict) and "content" in item:
						for c in item["content"]:
							if isinstance(c, dict) and "text" in c:
								parts.append(c["text"])
							elif isinstance(c, str):
								parts.append(c)
				if parts:
					return "\n".join(parts)
		except Exception:
			pass
		try:
			# legacy chat completions response
			return resp.choices[0].message.content.strip()
		except Exception:
			return "(응답을 파싱할 수 없습니다.)"

	@st.cache_data
	def send_conversation(copy_history, api_key: str):
		if not api_key:
			return "API Key가 필요합니다."
		try:
			client = OpenAI(api_key=api_key)
			# Use Responses API; pass messages if available
			# copy_history is list of dicts with role/content
			messages = copy_history
			resp = client.responses.create(model="gpt-4o-mini", messages=messages)
			return extract_text_from_response(resp)
		except Exception as e:
			return f"오류 발생: {e}"

	# display chat history
	for msg in st.session_state.chat_history:
		role = msg.get("role", "user")
		content = msg.get("content", "")
		if hasattr(st, "chat_message"):
			try:
				with st.chat_message(role):
					st.write(content)
			except Exception:
				st.write(f"**{role}**: {content}")
		else:
			st.write(f"**{role}**: {content}")

	if send and user_input:
		# append user message
		st.session_state.chat_history.append({"role": "user", "content": user_input})
		with st.spinner("응답 생성 중..."):
			# send a copy to avoid caching issues with mutable session state
			copy_hist = list(st.session_state.chat_history)
			reply = send_conversation(copy_hist, st.session_state.openai_api_key)
		st.session_state.chat_history.append({"role": "assistant", "content": reply})
		# Clear input after sending; Streamlit reruns automatically when session state changes
		st.session_state.chat_input = ""

