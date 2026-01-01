import streamlit as st
import os
from dotenv import load_dotenv
from datetime import date
import time
from typing import List, Optional, Dict, Any
import json
import pandas as pd
import io

from services.news_client import NewsClient, NewsAPIException, save_to_json, NewsItem
from services.text_extract import extract_and_clean
from services.summarizer import GeminiSummarizer, SummarizerException
from services.sentiment import GeminiSentimentAnalyzer, SentimentException, SentimentResult

load_dotenv()

st.set_page_config(layout="wide")

def main():
    st.title("뉴스 요약 & 감성 분석 앱")
    st.markdown("---")

    news_api_key = os.getenv("NEWS_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if 'processed_news' not in st.session_state:
        st.session_state.processed_news = []
    if 'selected_article_index' not in st.session_state:
        st.session_state.selected_article_index = None

    with st.sidebar:
        st.header("검색 조건")
        keyword = st.text_input("키워드", "AI", help="뉴스 기사를 검색할 키워드를 입력하세요.")
        # from_date = st.date_input("시작 날짜") # 나중에 추가
        # to_date = st.date_input("종료 날짜") # 나중에 추가
        summary_length = st.selectbox("요약 길이", ["short", "medium", "long"], help="생성될 요약문의 길이를 선택하세요.")
        
        st.subheader("감성 분석 설정")
        positive_threshold = st.slider("긍정 임계값", min_value=0.0, max_value=1.0, value=0.3, step=0.05,
                                       help="감성 점수가 이 값 이상이면 '긍정'으로 분류됩니다.")
        negative_threshold = st.slider("부정 임계값", min_value=-1.0, max_value=0.0, value=-0.3, step=0.05,
                                       help="감성 점수가 이 값 이하이면 '부정'으로 분류됩니다.")

        search_button = st.button("뉴스 검색 및 분석 실행")
        if st.session_state.processed_news:
            if st.button("결과 초기화"):
                st.session_state.processed_news = []
                st.session_state.selected_article_index = None
                st.experimental_rerun()


    if not news_api_key:
        st.error("NewsAPI 키가 설정되지 않았습니다. `.env` 파일을 확인해주세요.")
        return
    if not gemini_api_key:
        st.error("Gemini API 키가 설정되지 않았습니다. `.env` 파일을 확인해주세요.")
        return

    news_client = NewsClient(api_key=news_api_key)
    summarizer = GeminiSummarizer(api_key=gemini_api_key)
    
    try:
        sentiment_analyzer = GeminiSentimentAnalyzer(
            api_key=gemini_api_key,
            positive_threshold=positive_threshold,
            negative_threshold=negative_threshold
        )
    except ValueError as e:
        st.error(f"감성 분석기 설정 오류: {e}")
        return


    st.header("분석 결과")
    if search_button:
        if not keyword:
            st.warning("키워드를 입력해주세요.")
            return

        st.session_state.processed_news = [] # 새 검색 시 기존 결과 초기화
        st.session_state.selected_article_index = None

        progress_text = "뉴스 검색 및 분석 진행 중..."
        my_bar = st.progress(0, text=progress_text)

        try:
            # 1. 뉴스 검색
            my_bar.progress(10, text="뉴스 검색 중...")
            news_items: List[NewsItem] = news_client.get_news(keyword=keyword, page_size=10)
            my_bar.progress(30, text="뉴스 검색 완료. 본문 정제 및 AI 분석 준비 중...")

            if not news_items:
                st.warning("검색된 뉴스가 없습니다.")
                my_bar.empty()
                return
            
            # 2. 본문 정제, 요약 및 감성 분석
            for i, item in enumerate(news_items):
                current_progress = 30 + int((i / len(news_items)) * 60)
                my_bar.progress(current_progress, text=f"기사 {i+1}/{len(news_items)} 분석 중: {item.title}")

                item.processed_content = extract_and_clean(item)
                
                # 요약
                if item.processed_content:
                    try:
                        item.summary = summarizer.summarize(item.processed_content, summary_length)
                    except SummarizerException as e:
                        item.summary = f"요약 실패: {e}"
                        st.warning(f"'{item.title}' 요약 중 오류 발생: {e}")
                else:
                    item.summary = "요약할 본문 내용이 없습니다."
                
                # 감성 분석
                if item.processed_content:
                    try:
                        item.sentiment = sentiment_analyzer.analyze(item.processed_content)
                    except SentimentException as e:
                        item.sentiment = SentimentResult(label="neutral (실패)", score=0.0)
                        st.warning(f"'{item.title}' 감성 분석 중 오류 발생: {e}")
                else:
                    item.sentiment = SentimentResult(label="neutral (본문 없음)", score=0.0)
                
                st.session_state.processed_news.append(item)
            
            my_bar.progress(100, text="모든 뉴스 분석 완료!")
            time.sleep(1) # 잠시 완료 상태 보여주기
            my_bar.empty() # 진행률 바 숨기기
            

            # JSON 파일로 저장 (가공된 내용을 포함하여 저장)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"news_{keyword.replace(' ', '_')}_{timestamp}.json"
            filepath = save_to_json(news_items, "data", filename)
            
            st.success(f"{len(news_items)}개의 뉴스를 찾았으며, '{filepath}'에 저장했습니다.")
            st.markdown("---")

        except NewsAPIException as e:
            st.error(f"뉴스 검색 중 오류 발생: {e}")
            my_bar.empty()
        except Exception as e:
            st.error(f"알 수 없는 오류가 발생했습니다: {e}")
            my_bar.empty()
    
    # 처리된 뉴스 결과 표시 및 선택 UI
    if st.session_state.processed_news:
        st.subheader("분석된 뉴스 목록")
        
        # 다운로드 버튼
        col1, col2 = st.columns(2)
        with col1:
            json_data = json.dumps([item.asdict() for item in st.session_state.processed_news], ensure_ascii=False, indent=4)
            st.download_button(
                label="JSON으로 다운로드",
                data=json_data,
                file_name=f"news_analysis_{time.strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        with col2:
            # Pandas DataFrame으로 변환 후 CSV 생성
            df_data = []
            for item in st.session_state.processed_news:
                item_dict = item.asdict()
                if item_dict['sentiment']:
                    item_dict['sentiment_label'] = item_dict['sentiment']['label']
                    item_dict['sentiment_score'] = item_dict['sentiment']['score']
                del item_dict['sentiment'] # 중첩 딕셔너리 제거
                df_data.append(item_dict)

            df = pd.DataFrame(df_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig') # 한글 깨짐 방지
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="CSV로 다운로드",
                data=csv_data,
                file_name=f"news_analysis_{time.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("---")
        
        # 기사 목록 및 선택
        article_titles = [f"{i+1}. {item.title}" for i, item in enumerate(st.session_state.processed_news)]
        
        selected_title_option = st.selectbox(
            "상세 정보를 볼 기사를 선택하세요:",
            ["-- 기사를 선택하세요 --"] + article_titles,
            index=0
        )

        if selected_title_option != "-- 기사를 선택하세요 --":
            selected_idx = article_titles.index(selected_title_option)
            st.session_state.selected_article_index = selected_idx
        else:
            st.session_state.selected_article_index = None

        if st.session_state.selected_article_index is not None:
            selected_item = st.session_state.processed_news[st.session_state.selected_article_index]
            st.subheader(selected_item.title)
            st.write(f"**출처**: {selected_item.source_name}")
            st.write(f"**게시일**: {selected_item.published_at}")
            st.markdown(f"[기사 원문 링크]({selected_item.url})")
            
            # 감성 결과 표시
            if selected_item.sentiment:
                sentiment_color = "green" if selected_item.sentiment.label == "positive" else \
                                "red" if selected_item.sentiment.label == "negative" else "orange"
                st.markdown(
                    f"**감성**: <span style='color:{sentiment_color}; font-weight:bold'>{selected_item.sentiment.label}</span> "
                    f"(스코어: {selected_item.sentiment.score:.2f})",
                    unsafe_allow_html=True
                )
            else:
                st.info("감성 분석 결과를 가져올 수 없습니다.")

            if selected_item.summary:
                st.markdown("**요약**: ")
                st.write(selected_item.summary)
            else:
                st.info("요약된 내용을 가져올 수 없습니다.")
            
            with st.expander("정제된 본문 보기"):
                if selected_item.processed_content:
                    st.markdown("**정제된 본문**: ")
                    st.write(selected_item.processed_content)
                else:
                    st.info("정제된 본문 내용을 가져올 수 없습니다.")
            
            with st.expander("원문 (원시 데이터) 보기"):
                if selected_item.content:
                    st.markdown("**원문 (원본 API 응답)**: ")
                    st.write(selected_item.content)
                else:
                    st.info("원문 내용을 가져올 수 없습니다.")
        st.markdown("---")
    else:
        st.info("왼쪽 사이드바에서 검색 조건을 입력하고 '뉴스 검색 및 분석 실행' 버튼을 눌러주세요.")


if __name__ == "__main__":
    main()
