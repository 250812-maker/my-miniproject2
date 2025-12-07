import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import base64
import requests
import datetime
from audio_recorder_streamlit import audio_recorder

# 1. 환경 변수 로드
load_dotenv()

# STT 함수 (에러 처리 추가)
def request_stt(audio_data):
    endpoint = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=ko-KR&format=detailed"
    
    # API 키 검증
    api_key = os.getenv("AZURE_SPEECH_KEY")
    if not api_key:
        st.error("Azure Speech API 키가 설정되지 않았습니다.")
        return None
    
    header = {
        "Ocp-Apim-Subscription-Key": "3KDu9w9L3PsFSjcYcTqqkGKctaCoTCIWuvHvPqxd2niN2QpSk5TrJQQJ99BLACYeBjFXJ3w3AAAYACOGI0lI",
        "Content-Type": "audio/wav"
    }
    
    try:
        response = requests.post(endpoint, headers=header, data=audio_data, timeout=10)
        response.raise_for_status()
        response_json = response.json()
        text = response_json.get('DisplayText', '')
        return text
    except requests.exceptions.RequestException as e:
        st.error(f"음성 인식 오류: {str(e)}")
        return None
    except Exception as e:
        st.error(f"예상치 못한 오류: {str(e)}")
        return None

# TTS 함수 (에러 처리 추가)
def request_tts(text):
    endpoint = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    
    # API 키 검증
    api_key = os.getenv("AZURE_SPEECH_KEY")
    if not api_key:
        st.error("Azure Speech API 키가 설정되지 않았습니다.")
        return None
    
    headers = {
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
        "Ocp-Apim-Subscription-Key": "3KDu9w9L3PsFSjcYcTqqkGKctaCoTCIWuvHvPqxd2niN2QpSk5TrJQQJ99BLACYeBjFXJ3w3AAAYACOGI0lI"
    }
    
    body = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">
        <voice name="ko-KR-SunHiNeural">
            {text}
        </voice>
    </speak>"""
    
    try:
        response = requests.post(endpoint, headers=headers, data=body.strip(), timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"음성 합성 오류: {str(e)}")
        return None
    except Exception as e:
        st.error(f"예상치 못한 오류: {str(e)}")
        return None

# 페이지 설정
st.set_page_config(page_title="Teeni", page_icon="🌱", layout="wide")

# 배경색 변경 CSS
st.markdown("""
    <style>
    /* 메인 배경색 */
    .stApp {
        background-color: #B6DADA;
    }
    
    /* 사이드바 배경색 */
    [data-testid="stSidebar"] {
        background-color: #9BC7C7;
    }
    
    /* 입력 박스 배경색 */
    .stTextInput > div > div > input {
        background-color: white;
    }
    
    /* 텍스트 영역 배경색 */
    .stTextArea > div > div > textarea {
        background-color: white;
    }
    
    /* 채팅 입력창 배경색 */
    .stChatInput > div > div > textarea {
        background-color: white;
    }
    
    /* 셀렉트 박스 배경색 */
    .stSelectbox > div > div > select {
        background-color: white;
    }
    
    /* 날짜/시간 입력 배경색 */
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {
        background-color: white;
    }
    
    /* 파일 업로더 배경색 */
    [data-testid="stFileUploader"] {
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>청소년을 위한 AI 서비스 <span style='color: #008080;'>Teeni🌱</span></h1>", unsafe_allow_html=True)

######################################################

# Session State 초기화 (기능별 메시지 분리)
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "홈"
if "study_messages" not in st.session_state:
    st.session_state.study_messages = []
if "counsel_messages" not in st.session_state:
    st.session_state.counsel_messages = []
if "calendar_events" not in st.session_state:
    st.session_state.calendar_events = []
if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

# Azure OpenAI 클라이언트 설정
try:
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OAI_KEY"),
        api_version="2025-01-01-preview",
        azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT")
    )
except Exception as e:
    st.error(f"Azure OpenAI 클라이언트 초기화 실패: {str(e)}")
    st.stop()

# ===== 사이드바 =====
with st.sidebar:
    st.header("메뉴")
    
    # 메뉴 버튼들
    if st.button("🏠 홈", use_container_width=True):
        st.session_state.current_menu = "홈"
        st.rerun()
    
    if st.button("📚 학습 지원", use_container_width=True):
        st.session_state.current_menu = "학습 지원"
        st.rerun()
    
    if st.button("💬 심리 상담", use_container_width=True):
        st.session_state.current_menu = "심리 상담"
        st.rerun()
    
    if st.button("📅 일정 관리", use_container_width=True):
        st.session_state.current_menu = "일정 관리"
        st.rerun()
    
    st.divider()
    
    # 대화 초기화 버튼
    if st.button("🔄 새 대화 시작", use_container_width=True):
        if st.session_state.current_menu == " ":
            st.session_state.study_messages = []
        elif st.session_state.current_menu == "심리 상담":
            st.session_state.counsel_messages = []
        st.session_state.audio_processed = False
        st.rerun()
    
    st.divider()
    
    # 설정 옵션
    st.subheader("⚙️ 설정")
    temperature = st.slider("응답 창의성", 0.0, 1.0, 0.5, 0.1)
    max_tokens = st.number_input("최대 응답 길이", 100, 2000, 700, 100)
    
    st.divider()
    
    # 정보 표시
    st.subheader("ℹ️ 안내")
    st.info("Teeni에 오신 것을 환영합니다!")
    
    # 대화 횟수 표시
    if st.session_state.current_menu == " ":
        message_count = len([m for m in st.session_state.study_messages if m["role"] == "user"])
    elif st.session_state.current_menu == "심리 상담":
        message_count = len([m for m in st.session_state.counsel_messages if m["role"] == "user"])
    else:
        message_count = 0
    st.metric("대화 횟수", message_count)

# ===== 메인 컨텐츠 =====

# 홈 화면
if st.session_state.current_menu == "홈":
    st.subheader("Teeni와 함께 밝은 내일로!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📚 학습 지원")
        st.write("검정고시 준비, 언어·수리·외국어 학습을 도와드립니다.")
        if st.button("학습 시작하기", key="home_study"):
            st.session_state.current_menu = " "
            st.rerun()
    
    with col2:
        st.markdown("### 💬 심리 상담")
        st.write("음성으로 편하게 고민을 나누고 상담받으세요.")
        if st.button("상담 시작하기", key="home_counsel"):
            st.session_state.current_menu = "심리 상담"
            st.rerun()
    
    with col3:
        st.markdown("### 📅 일정 관리")
        st.write("학습 계획과 일정을 체계적으로 관리하세요.")
        if st.button("일정 관리하기", key="home_calendar"):
            st.session_state.current_menu = "일정 관리"
            st.rerun()

# 학습 지원 화면
elif st.session_state.current_menu == " ":
    st.subheader("📚 학습 지원")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎓 검정고시 정보", "언어 학습", "수리 학습", "외국어 학습"])
    
    with tab1:
        st.write("### 검정고시 시험 정보")
        st.info("검정고시와 관련된 질문을 해보세요!")
        
    with tab2:
        st.write("### 언어(국어) 학습")
        st.info("국어 학습과 관련된 질문을 해보세요!")
        
    with tab3:
        st.write("### 수리(수학) 학습")
        st.info("수학 학습과 관련된 질문을 해보세요!")
        
    with tab4:
        st.write("### 외국어(영어) 학습")
        st.info("영어 학습을 도와드립니다!")
    
    # 대화 내용 출력
    for message in st.session_state.study_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("학습 관련 질문을 입력하세요..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.study_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            system_message = "너는 학교 밖 청소년을 위한 학습 지원 AI입니다. 검정고시 정보를 알려주세요. 정확한 내용으로 학습을 도와주세요."
            
            try:
                response = client.chat.completions.create(
                    model="8ai051-gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_message}
                    ] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.study_messages
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                assistant_reply = response.choices[0].message.content
                st.markdown(assistant_reply)
                st.session_state.study_messages.append({"role": "assistant", "content": assistant_reply})
            except Exception as e:
                st.error(f"응답 생성 중 오류 발생: {str(e)}")

# 심리 상담 화면
elif st.session_state.current_menu == "심리 상담":
    st.subheader("💬 심리 상담 (음성 지원)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### 🎤 음성으로 상담하기")
        st.info("🔴 녹음 버튼을 눌러 고민을 말씀해주세요. 음성으로 답변해드립니다.")
        
        # 음성 녹음
        audio_bytes = audio_recorder(
            text="🎤 녹음 시작",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=3.0,
            sample_rate=16000
        )
        
        if audio_bytes and not st.session_state.audio_processed:
            st.audio(audio_bytes, format='audio/wav')
            
            with st.spinner("음성을 인식하고 있습니다..."):
                recognized_text = request_stt(audio_bytes)
                
                if recognized_text:
                    st.success(f"✅ 인식된 내용: {recognized_text}")
                    st.session_state.counsel_messages.append({"role": "user", "content": recognized_text})
                    
                    with st.spinner("답변을 생성하고 있습니다..."):
                        system_message = "너는 청소년 심리 상담 전문가입니다. 공감하고 친절하게 상담해주세요."
                        
                        try:
                            response = client.chat.completions.create(
                                model="8ai051-gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": system_message}
                                ] + [
                                    {"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.counsel_messages
                                ],
                                temperature=0.7,
                                max_tokens=max_tokens
                            )
                            assistant_reply = response.choices[0].message.content
                            st.session_state.counsel_messages.append({"role": "assistant", "content": assistant_reply})
                            
                            # TTS 처리
                            audio_content = request_tts(assistant_reply)
                            
                            if audio_content:
                                st.success("🔊 음성 답변이 준비되었습니다!")
                                st.audio(audio_content, format='audio/wav')
                            
                            st.markdown(f"**답변:** {assistant_reply}")
                            st.session_state.audio_processed = True
                        except Exception as e:
                            st.error(f"응답 생성 중 오류 발생: {str(e)}")
        
        # 음성이 새로 녹음되면 플래그 리셋
        if not audio_bytes:
            st.session_state.audio_processed = False
        
        st.divider()
        
        # 파일 업로드 옵션
        st.write("#### 또는 음성 파일 업로드")
        audio_file = st.file_uploader("음성 파일 업로드 (WAV)", type=['wav'], key="audio_upload")
        
        if audio_file is not None:
            st.audio(audio_file, format='audio/wav')
            
            if st.button("🎤 업로드한 음성 인식"):
                with st.spinner("음성을 인식하고 있습니다..."):
                    audio_data = audio_file.read()
                    recognized_text = request_stt(audio_data)
                    
                    if recognized_text:
                        st.success(f"✅ 인식된 내용: {recognized_text}")
                        st.session_state.counsel_messages.append({"role": "user", "content": recognized_text})
                        
                        with st.spinner("답변을 생성하고 있습니다..."):
                            system_message = "너는 청소년 심리 상담 전문가입니다. 공감하고 따뜻하게 상담해주세요."
                            
                            try:
                                response = client.chat.completions.create(
                                    model="8ai051-gpt-4o-mini",
                                    messages=[
                                        {"role": "system", "content": system_message}
                                    ] + [
                                        {"role": m["role"], "content": m["content"]}
                                        for m in st.session_state.counsel_messages
                                    ],
                                    temperature=0.7,
                                    max_tokens=max_tokens
                                )
                                assistant_reply = response.choices[0].message.content
                                st.session_state.counsel_messages.append({"role": "assistant", "content": assistant_reply})
                                
                                audio_content = request_tts(assistant_reply)
                                
                                if audio_content:
                                    st.success("🔊 음성 답변이 준비되었습니다!")
                                    st.audio(audio_content, format='audio/wav')
                                
                                st.markdown(f"**답변:** {assistant_reply}")
                            except Exception as e:
                                st.error(f"응답 생성 중 오류 발생: {str(e)}")
    
    with col2:
        st.write("### 💡 상담 팁")
        st.markdown("""
        - 편안하게 고민을 말씀해주세요
        - 천천히 또박또박 말씀해주시면 더 정확합니다
        - 조용한 곳에서 녹음하면 좋습니다
        - 언제든 대화를 중단하고 쉬어도 괜찮아요
        """)
    
    st.divider()
    
    # 텍스트 상담 옵션
    st.write("### ✍️ 텍스트로 상담하기")
    
    # 대화 내용 출력
    for message in st.session_state.counsel_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 텍스트 입력
    if prompt := st.chat_input("고민을 텍스트로 입력하세요..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.counsel_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            system_message = "너는 청소년 심리 상담 전문가입니다. 공감하고 따뜻하게 상담해주세요."
            
            try:
                response = client.chat.completions.create(
                    model="8ai051-gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_message}
                    ] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.counsel_messages
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                assistant_reply = response.choices[0].message.content
                st.markdown(assistant_reply)
                st.session_state.counsel_messages.append({"role": "assistant", "content": assistant_reply})
            except Exception as e:
                st.error(f"응답 생성 중 오류 발생: {str(e)}")

# 일정 관리 화면
elif st.session_state.current_menu == "일정 관리":
    st.subheader("📅 일정 관리")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("### ➕ 새 일정 추가")
        
        with st.form("add_event_form"):
            event_date = st.date_input("날짜")
            event_time = st.time_input("시간")
            event_title = st.text_input("일정 제목")
            event_description = st.text_area("상세 내용")
            event_category = st.selectbox("카테고리", ["학습", "상담", "개인", "기타"])
            
            submitted = st.form_submit_button("일정 추가")
            
            if submitted and event_title:
                new_event = {
                    "date": event_date.strftime("%Y-%m-%d"),
                    "time": event_time.strftime("%H:%M"),
                    "title": event_title,
                    "description": event_description,
                    "category": event_category
                }
                st.session_state.calendar_events.append(new_event)
                st.success("✅ 일정이 추가되었습니다!")
                st.rerun()
    
    with col2:
        st.write("### 📋 내 일정 목록")
        
        if st.session_state.calendar_events:
            sorted_events = sorted(st.session_state.calendar_events, key=lambda x: (x["date"], x["time"]))
            
            for idx, event in enumerate(sorted_events):
                with st.expander(f"{event['date']} {event['time']} - {event['title']}"):
                    st.write(f"**카테고리:** {event['category']}")
                    st.write(f"**내용:** {event['description']}")
                    
                    if st.button("삭제", key=f"delete_{idx}"):
                        st.session_state.calendar_events.remove(event)
                        st.rerun()
        else:
            st.info("등록된 일정이 없습니다. 새 일정을 추가해보세요!")
    
    st.divider()
    
    # 캘린더 뷰
    st.write("### 📆 이번 주 일정")
    
    today = datetime.date.today()
    
    week_events = [e for e in st.session_state.calendar_events 
                   if datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() >= today
                   and datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() <= today + datetime.timedelta(days=7)]
    
    if week_events:
        for event in sorted(week_events, key=lambda x: (x["date"], x["time"])):
            st.markdown(f"- **{event['date']} {event['time']}** | {event['title']} ({event['category']})")
    else:
        st.info("이번 주 일정이 없습니다.")