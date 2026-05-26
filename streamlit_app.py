# Streamlit + OpenAI 간단 LLM QA 웹앱
import re
from pathlib import Path

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


@st.cache_data
def load_regulation_text(pdf_path: str) -> str:
	path = Path(pdf_path)
	if not path.exists():
		return ""
	try:
		from pypdf import PdfReader
	except ImportError:
		return ""
	text_parts = []
	try:
		reader = PdfReader(path)
		for page in reader.pages:
			page_text = page.extract_text() or ""
			text_parts.append(page_text)
		return "\n".join(text_parts)
	except Exception:
		return ""


@st.cache_data
def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200):
	if not text:
		return []
	text = text.replace("\n", " ")
	chunks = []
	start = 0
	while start < len(text):
		chunk = text[start:start + chunk_size].strip()
		if chunk:
			chunks.append(chunk)
		start += chunk_size - overlap
	return chunks


def find_relevant_chunks(question: str, chunks: list[str], top_n: int = 4) -> list[str]:
	if not question or not chunks:
		return []
	query = question.lower().strip()
	terms = [t for t in re.findall(r"[가-힣A-Za-z0-9]+", query) if t]
	scores = []
	for chunk in chunks:
		text = chunk.lower()
		score = sum(1 for term in terms if term in text)
		scores.append((score, chunk))
	scores.sort(reverse=True, key=lambda x: x[0])
	return [chunk for score, chunk in scores[:top_n] if score > 0]


def build_library_prompt(question: str, snippets: list[str], history: list[dict]) -> str:
	context = "\n\n".join(snippets) if snippets else "(규정집에서 관련 내용을 찾을 수 없습니다.)"
	history_text = "\n".join(
		f"사용자: {item['content']}" if item.get('role') == 'user' else f"도서관 챗봇: {item['content']}"
		for item in history
	)
	return (
		"당신은 국립부경대학교 도서관 규정집을 기반으로 답변하는 챗봇입니다."
		" 아래 규정집 내용을 참고하여 답변하세요. 규정집에 없으면 '규정집에서 찾을 수 없습니다.'라고 답해주세요.\n\n"
		f"규정집 관련 내용:\n{context}\n\n"
		f"대화 기록:\n{history_text}\n\n"
		f"질문: {question}\n"
	)


def parse_chat_response(resp) -> str:
	try:
		return resp.choices[0].message.content.strip()
	except Exception:
		try:
			return str(resp)
		except Exception:
			return "(응답을 파싱할 수 없습니다.)"


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
	st.header("국립부경대학교 도서관 챗봇")
	st.write("규정집을 기반으로 도서관 휴관일, 학부생 대출 권수 등을 답변합니다.")

	regulation_path = Path("/workspaces/a/국립부경대학교 도서관 규정.pdf")
	regulation_text = load_regulation_text(str(regulation_path))
	if not regulation_text:
		st.error("도서관 규정집 PDF를 읽을 수 없습니다. 파일 경로와 라이브러리 설치를 확인해 주세요.")
		st.stop()

	regulation_chunks = chunk_text(regulation_text)

	if "chat_history" not in st.session_state:
		st.session_state.chat_history = []

	col1, col2 = st.columns([1, 3])
	with col1:
		if st.button("Clear"):
			st.session_state.chat_history = []
	with col2:
		st.write("대화를 초기화하려면 Clear를 누르세요.")

	with st.form("library_chat_form"):
		user_input = st.text_input("질문을 입력하세요", key="library_chat_input")
		submit = st.form_submit_button("Send")

	if submit and user_input:
		st.session_state.chat_history.append({"role": "user", "content": user_input})
		relevant = find_relevant_chunks(user_input, regulation_chunks)
		if not relevant:
			st.warning("질문과 관련된 규정집 내용을 찾지 못했습니다. 가능한 한 가장 가까운 답변을 제공합니다.")
		prompt_text = build_library_prompt(user_input, relevant, st.session_state.chat_history)
		if not st.session_state.openai_api_key:
			reply = "OpenAI API Key를 입력하세요."
		else:
			try:
				client = OpenAI(api_key=st.session_state.openai_api_key)
				resp = client.chat.completions.create(
					model="gpt-3.5-turbo",
					messages=[
						{"role": "system", "content": "당신은 국립부경대학교 도서관 규정집을 기반으로 답변하는 챗봇입니다. 규정집에 없는 내용은 답변하지 마세요."},
						{"role": "user", "content": prompt_text},
					],
					max_tokens=512,
					temperature=0.2,
				)
				reply = parse_chat_response(resp)
			except Exception as e:
				reply = f"오류 발생: {e}"
		st.session_state.chat_history.append({"role": "assistant", "content": reply})

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

