# LLM QA Streamlit 앱

간단한 Streamlit 웹앱으로 사용자의 질문을 받아 OpenAI LLM 응답을 출력합니다. OpenAI API Key를 웹 페이지에서 입력하도록 되어 있으며, 입력된 키는 `st.session_state`에 저장되어 페이지를 옮겨도 유지됩니다. 동일한 입력(질문+API Key)은 `@st.cache_data`로 캐시되어 재실행 시 빠르게 결과를 반환합니다.

파일
- [streamlit_app.py](streamlit_app.py#L1-L200)

로컬 실행
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

GitHub에 푸시하기
1. 새 저장소를 만들거나 기존 저장소에 커밋합니다.
```
git init
git add .
git commit -m "Add Streamlit LLM QA app"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

Streamlit Cloud에 배포하기
1. [streamlit.io](https://streamlit.io) 계정으로 로그인합니다.
2. "Deploy an app"에서 GitHub 저장소를 연결하고, 브랜치(`main`)와 앱 파일(`streamlit_app.py`)을 선택합니다.
3. `requirements.txt`를 사용해 의존성을 설치합니다. 배포 후 앱 URL이 생성됩니다.

제출
- GitHub 저장소 URL
- Streamlit Cloud에서 생성된 앱 URL
