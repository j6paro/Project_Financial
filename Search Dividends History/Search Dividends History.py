import yfinance as yf
from tkinter import *
from tkinter import filedialog
from tkinter import font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import datetime

df_savefile = pd.DataFrame()  # 엑셀 파일로 저장할 데이터프레임. 처음엔 아무것도 없음


# 배당금, 배당률, 종가 받아오는 함수
def scraping_stock_data():
    global df_savefile

    ### 주식 데이터 스크래핑하고 배당금, 배당률 시각화
    ticker = str(entry_ticker.get()).upper()  # 엔트리에 입력된 특정 종목 티커 받아오기
    stock = yf.Ticker(ticker)  # 주식 데이터 다운로드

    # 주식 정보 데이터프레임 만들기
    df_stockdata = stock.history(interval="1d", period="max")  # 특정 종목 정보 받아오기
    df_stockdata = df_stockdata.reset_index()  # 인덱스 초기화
    df_stockdata["Year"] = (
        df_stockdata["Date"].astype("str").str.split("-").str[0]
    )  # 연도 컬럼 생성

    # 전처리용 데이터프레임 만들기
    df_preprocessing = df_stockdata[
        df_stockdata.Dividends != 0
    ]  # Dividends가 0인 행 모두 삭제
    df_preprocessing = df_preprocessing.reset_index()  # 인덱스 초기화
    df_preprocessing.drop(["index"], axis=1, inplace=True)
    pd.to_datetime(df_preprocessing["Date"])  # 데이터타입 datetime으로 변경

    df_pivot_dividends = pd.pivot_table(
        df_preprocessing, values="Dividends", index="Year", aggfunc=np.sum
    )  # 배당금 피벗 테이블 만들기
    df_pivot_price = pd.pivot_table(
        df_preprocessing, values="Close", index="Year", aggfunc=np.mean
    )  # 종가 피벗 테이블 만들기

    # 종가 테이블, 배당금 테이블 join 하기
    df_merged = pd.merge(
        df_pivot_dividends, df_pivot_price, on="Year", how="inner"
    )  # 인덱스로 join 하기
    df_merged["Dividends yield rate"] = round(
        (df_merged["Dividends"] / df_merged["Close"]) * 100, 1
    )  # 배당률 컬럼 생성
    df_merged = df_merged.reset_index()  # 인덱스 초기화
    df_savefile = df_stockdata  # 저장할 데이터프레임 만들어 주기
    df_savefile["Date"] = (
        df_savefile["Date"].astype("str").str.split("-").str[0]
    )  # 타임존은 엑셀로 저장이 안 된다.

    make_graph(df_merged, ticker)

    ### 현재 종가 기준 배당률 구하기
    now = datetime.datetime.now()  # 현재 시간
    now_transform = str(now).split()[0]  # 현재 시간을 yyyy-mm-dd 형식으로
    date_lastclose = str(df_stockdata["Date"].iloc[-1]).split()[
        0
    ]  # 가장 최근 종가 날짜
    price_last_close = df_stockdata["Close"].iloc[-1]  # 가장 최근 종가
    date_last_dividends = str(df_preprocessing["Date"].iloc[-1])  # 마지막 배당일

    if (
        str(now).split()[0][:7] == date_last_dividends[:7]
    ):  # 만약 이번달에 배당이 나옴 -> 배당금합 = 11개월 전~이번달 배당합
        start_date = (
            str(now.year - 1) + "-" + str(now.month + 1).zfill(2) + "-01"
        )  # 시작일을 11개월 전 1일로
        df_trailing_dividends = df_preprocessing[
            df_preprocessing["Date"].bewteen(start_date, now_transform)
        ]  # 최근 1년 데이터프레임
        trailing_dividends_yield_rate = (
            df_trailing_dividends["Dividends"].sum / price_last_close
        ) * 100  # 최근 1년 배당률 구하기
    else:
        start_date = (
            str(now.year - 1) + "-" + str(now.month).zfill(2) + "-01"
        )  # 시작일을 11개월 전 1일로
        df_trailing_dividends = df_preprocessing[
            df_preprocessing["Date"].between(start_date, now_transform)
        ]  # 최근 1년 데이터프레임
        trailing_dividends_yield_rate = (
            df_trailing_dividends["Dividends"].sum() / price_last_close
        ) * 100  # 최근 1년 배당률 구하기
    current_dividends_yield_rate.set(
        f"마지막 종가일({date_lastclose})기준 배당률 : {round(trailing_dividends_yield_rate,1)}%"
    )


# 시각화 함수
def make_graph(df, ticker):
    for widget in frame_3.winfo_children():  # 그래프 매번 새로 그리기
        widget.destroy()

    # 한글 폰트 설정
    plt.rcParams["font.family"] = "Malgun Gothic"  # Windows의 맑은 고딕
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 그래프1
    ax1.set_xlabel("년도")  # 수정. x축 label
    ax1.set_ylabel("배당률", color="red")  # 수정. 그래프1 y축 label
    (line1,) = ax1.plot(
        df["Year"],
        df["Dividends yield rate"],
        "ro--",
        markersize=4,
        label="배당률",
        color="red",
    )  # 그래프1 그리기
    ax1.tick_params(axis="y", labelcolor="red")  # 그래프1 y축 색상 지정

    # 그래프1 숫자표시 : x축, y축 좌표에 값을 텍스트로 표시
    for i, v in enumerate(
        df.index
    ):  # x축 리스트에서 (인덱스, x축 리스트[인덱스]에 해당하는 value)를 가져온다.
        plt.text(
            v,
            df["Dividends yield rate"][i],
            round(
                df["Dividends yield rate"][i], 2
            ),  # x축 리스트[인덱스] : x축 좌표, y축 리스트[인덱스] : y축 좌표, y축 리스트[인덱스] : 표시할 숫자
            fontsize=9,  # 텍스트 크기
            color="red",  # 텍스트 색깔
            horizontalalignment="center",  # 수평 위치 (left, center, right)
            verticalalignment="bottom",  # 수직 위치 (top, center, bottom)
            # rotation=70 # 텍스트 각도
        )

    plt.xticks(rotation=45, fontsize=8)  # 그래프 2 그리기 이전에 해야 x축 45도 돌아감

    # 그래프2
    ax2 = ax1.twinx()  # 두 번째 y축 생성
    ax2.set_ylabel("배당금", color="blue")  # 수정. 그래프2 y축 label
    line2 = ax2.bar(
        df["Year"], df["Dividends"], label=ticker + "_배당금", color="blue"
    )  # 그래프2 그리기
    ax2.tick_params(axis="y", labelcolor="blue")  # 그래프2 y축 색상 지정

    # 그래프2 숫자표시
    for i, v in enumerate(df.index):
        plt.text(
            v,
            df["Dividends"][i],
            round(df["Dividends"][i], 2),
            fontsize=9,
            color="blue",
            horizontalalignment="center",
            verticalalignment="center",
            # rotation=45
        )

    # 제목 및 범례 추가
    lines_labels = line1.get_label(), line2.get_label()
    handles = [line1, line2]
    plt.legend(handles, lines_labels, loc="upper left", fontsize=10, frameon=True)
    ax1.set_zorder(
        ax2.get_zorder() + 10
    )  # 그래프1 zorder를 그래프2 zorder보다 무조건 높게. zorder 낮을수록 먼저 그려짐
    ax1.patch.set_visible(False)  # 그래프1 레이어 투명하게
    plt.title(f"배당률 & 배당금 : {ticker}")  # 수정. 그래프 제목
    fig.tight_layout()  # 레이아웃 조정

    canvas_graph = FigureCanvasTkAgg(fig, frame_3)
    canvas_graph.get_tk_widget().pack(side=LEFT, fill=BOTH)


def save_graph():  # 그래프 저장 위치 정하기
    filename = filedialog.asksaveasfilename(
        initialfile="Untitled.png",
        defaultextension=".png",
        filetypes=[("All Files", "*.*"), ("Portable Graphics Format", "*.png")],
    )
    plt.savefig(filename)


def save_excelfile():  # 엑셀 파일 저장 위치 정하기
    filename = filedialog.asksaveasfilename(
        initialfile="Untitled.xlsx",
        defaultextension=".xlsx",
        filetypes=[("All Files", "*.*"), ("Excel 통합 문서", "*.xlsx")],
    )
    df_savefile.to_excel(filename, index=True, index_label="Year")


# 윈도우 생성
window = Tk()
window.title("Search Dividends History")  # 윈도우 이름
window.geometry("1200x600")  # 윈도우 크기

# tkinter 폰트 맑은 고딕으로
gui_font = font.Font(family="맑은 고딕", size=25)

# 프레임 생성
frame_1 = Frame(
    master=window, relief=RAISED
)  # 티커 검색 버튼, 엑셀 저장 버튼, 그래프 저장 버튼 프레임
frame_2 = Frame(master=window)  # 마지막 종가 기준 배당률 출력
frame_3 = Frame(master=window)  # 그래프 출력 프레임

# 레이블 위젯 : 티커를 입력하세요
label_ticker = Label(master=frame_1, text="Tiker : ", font=gui_font)

# 레이블 위젯 : 마지막 종가 기준 배당률 출력
current_dividends_yield_rate = StringVar()
label_current_dividends_yield_rate = Label(
    master=frame_2, textvariable=current_dividends_yield_rate, font=gui_font
)

# 엔트리 위젯 : 티커 입력. 테스트로는 x의 몇 제곱인지
entry_ticker = Entry(
    master=frame_1, fg="black", bg="white", width=20, justify=CENTER, font=gui_font
)

# 버튼 위젯 : 검색, 엑셀 파일 저장, 그래프 저장
button_search = Button(
    master=frame_1,
    text="검색",
    bg="white",
    fg="black",
    width=10,
    height=2,
    command=scraping_stock_data,
)  # 검색 버튼

button_download_excel = Button(
    master=frame_1,
    text="엑셀 파일 저장",
    bg="white",
    fg="black",
    width=20,
    height=2,
    command=save_excelfile,
)  # lambda: print("엑셀 파일이 저장되었습니다.")) # 엑셀 파일로 저장하는 버튼

button_download_graph = Button(
    master=frame_1,
    text="그래프 저장",
    bg="white",
    fg="black",
    width=20,
    height=2,
    command=save_graph,
)  # 이미지 저장하는 버튼


# 처음에 빈화면 띄워놓기
fig, ax = plt.subplots(figsize=(8, 6))
canvas_graph = FigureCanvasTkAgg(fig, frame_3)
canvas_graph.get_tk_widget().pack(side=LEFT, fill=BOTH)

# 프레임 배치
frame_1.pack()  # 티커 검색, 그래프, 엑셀 저장 버튼
frame_2.pack()  # 마지막 종가 기준 배당률
frame_3.pack()  # 역대 배당률, 배당금 시각화

# 라벨, 엔트리 배치
label_ticker.pack(side=LEFT)  # 티커 검색 라벨 배치
entry_ticker.pack(side=LEFT)  # 티커 검색 엔트리 배치
label_current_dividends_yield_rate.pack(side=LEFT)  # 마지막 종가 기준 배당률 라벨 배치

# 버튼 배치
button_search.pack(side=LEFT)
button_download_excel.pack(side=LEFT)
button_download_graph.pack(side=LEFT)

window.mainloop()
