# app.py
# 실행 방법:
# 1. pip install streamlit opencv-python moviepy librosa numpy pillow imagehash
# 2. streamlit run app.py

import streamlit as st
import tempfile
import cv2
import numpy as np
import imagehash
from PIL import Image
from moviepy.editor import VideoFileClip
import librosa
import os

st.set_page_config(page_title="영상 저작권 유사도 분석기", layout="wide")

st.title("🎬 영상 저작권 유사도 분석기")
st.write("원본 영상과 편집 영상을 업로드한 뒤 분석 버튼을 눌러주세요.")

# -----------------------------
# 업로드 영역
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    original_video = st.file_uploader(
        "📁 원본 영상 업로드",
        type=["mp4", "mov", "avi", "mkv"]
    )

with col2:
    edited_video = st.file_uploader(
        "📁 편집 영상 업로드",
        type=["mp4", "mov", "avi", "mkv"]
    )

# -----------------------------
# 영상 저장 함수
# -----------------------------
def save_uploaded_file(uploaded_file):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(uploaded_file.read())
    return temp_file.name

# -----------------------------
# 프레임 추출
# -----------------------------
def extract_frames(video_path, interval=30):
    cap = cv2.VideoCapture(video_path)
    frames = []

    count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if count % interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            frames.append(pil_img)

        count += 1

    cap.release()
    return frames

# -----------------------------
# 영상 해시 유사도 분석
# -----------------------------
def compare_video_frames(video1, video2):
    frames1 = extract_frames(video1)
    frames2 = extract_frames(video2)

    hashes1 = [imagehash.phash(frame) for frame in frames1]
    hashes2 = [imagehash.phash(frame) for frame in frames2]

    similarities = []

    min_len = min(len(hashes1), len(hashes2))

    for i in range(min_len):
        diff = hashes1[i] - hashes2[i]
        similarity = max(0, 100 - (diff * 2))
        similarities.append(similarity)

    if similarities:
        return round(np.mean(similarities), 2)

    return 0

# -----------------------------
# 오디오 추출
# -----------------------------
def extract_audio(video_path, output_audio):
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(output_audio, logger=None)

# -----------------------------
# 오디오 유사도 분석
# -----------------------------
def compare_audio(video1, video2):
    audio1 = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    audio2 = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

    extract_audio(video1, audio1)
    extract_audio(video2, audio2)

    y1, sr1 = librosa.load(audio1)
    y2, sr2 = librosa.load(audio2)

    mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1)
    mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2)

    min_shape = min(mfcc1.shape[1], mfcc2.shape[1])

    mfcc1 = mfcc1[:, :min_shape]
    mfcc2 = mfcc2[:, :min_shape]

    similarity = np.corrcoef(mfcc1.flatten(), mfcc2.flatten())[0, 1]

    os.remove(audio1)
    os.remove(audio2)

    return round(max(0, similarity) * 100, 2)

# -----------------------------
# 분석 버튼
# -----------------------------
if st.button("🔍 분석 시작"):

    if original_video and edited_video:

        with st.spinner("영상 분석 중입니다..."):

            original_path = save_uploaded_file(original_video)
            edited_path = save_uploaded_file(edited_video)

            # 영상 유사도
            video_similarity = compare_video_frames(
                original_path,
                edited_path
            )

            # 오디오 유사도
            audio_similarity = compare_audio(
                original_path,
                edited_path
            )

            # 최종 점수
            final_score = round(
                (video_similarity * 0.6) +
                (audio_similarity * 0.4),
                2
            )

        st.success("분석 완료!")

        st.subheader("📊 분석 결과")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🎞 영상 유사도", f"{video_similarity}%")

        with col2:
            st.metric("🎵 오디오 유사도", f"{audio_similarity}%")

        with col3:
            st.metric("⚠ 최종 유사도", f"{final_score}%")

        # 위험도 표시
        if final_score >= 85:
            st.error("저작권 위험도: 매우 높음")
        elif final_score >= 60:
            st.warning("저작권 위험도: 중간")
        else:
            st.success("저작권 위험도: 낮음")

        # 임시 파일 삭제
        os.remove(original_path)
        os.remove(edited_path)

    else:
        st.warning("두 개의 영상을 모두 업로드해주세요.")
