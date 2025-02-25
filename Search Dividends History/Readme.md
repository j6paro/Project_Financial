# 1. 개요

## 1-1. 동기
\- 배당 귀족주들의 배당 이력을 시각화하는 코드를 작성하면서 나스닥에 상장된 모든 종목의 배당 이력을 손쉽게 보고 싶다는 생각이 들었고, 코드로 구현했다.  

## 1-2. 프로그램 설명
![image](https://github.com/user-attachments/assets/8798b09c-b348-4844-85e4-f972cec4589c)

#### 1. 프로그램에는 다음의 기능들을 담았다.  
(1) 나스닥에 상장된 종목의 역대 배당금, 배당률 시각화하여 조회  
\- 원하는 종목의 티커를 입력 후 검색 버튼 클릭하여 조회 가능  
\- 배당률은 배당금을 당해의 종가 평균으로 나눔  
(2) 시각화된 그래프 이미지 다운로드  
\- 그래프 저장 버튼 클릭  
(3) 종목의 연도별 배당금, 배당률, 종가 평균 데이터 엑셀 파일로 다운로드  
\- 엑셀 파일 저장 버튼 클릭

#### 2. 화면 설명
(1) 배당금 이력 조회하고 싶은 티커 입력 (대, 소문자 상관 없음)  
(2) 티커 입력 후 검색 버튼 클릭  
(3) '엑셀 파일 저장' 버튼 클릭 시 해당 종목 데이터 엑셀 파일로 저장  
(4) '그래프 저장' 버튼 클릭 시 해당 종목 그래프 이미지 파일로 저장 

# 2. 코드

## 2-1. 전체적인 구성

#### 1. yfinance로 종목 데이터 스크래핑해서 배당금, 배당률 이력 계산하여 데이터프레임에 정리
#### 2. 배당금, 배당률 이력 시각화
#### 3. 위 기능들을 GUI로 구현

## 2-2. Search Dvididends History.ipynb

\- 해당 코드를 부분별로 나눔  

### 2-2-1. 라이브러리 import  
```
import yfinance as yf
from tkinter import *
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
```
\- yfinance : 야후 파이낸스에서 주식 기본 지표들을 스크래핑하기 위해 import 한다. 그런데 너무 많이 스크래핑 요청을 보내다 보면 야후 파이낸스에서 이를 봇으로 감지하는지 종종 알 수 없는 이유로 스크래핑이 중간에 멈추기도 한다.  
\- pandas : yfinance에서 수집한 배당금, 종가 데이터를 가공해 데이터프레임을 만들고 이를 저장한다.  
\- matplotlib.pyplot, FigureCanvasTkAgg : 시각화에 사용, FigureCanvasTkAgg는 matplotlib로 시각화한 그래프와 tkinter의 연결에 사용  
\- tinker, filedialog : 보기에 편하도록하려는 목적도 있고, 프로그램을 exe 파일로 배포하기 위해 GUI를 도입했다. filedialog는 그래프, 엑셀 파일 저장하는 창을 띄우는데 사용된다.  

### 2-2-2. yfinance로 배당률, 배당금 수집하여 데이터프레임 생성
```
df_savefile = pd.DataFrame()  # 엑셀 파일로 저장할 데이터프레임. 처음엔 아무것도 없음

# 배당금, 배당률, 종가 받아오는 함수
def scraping_stock_data():
    global df_savefile

    ticker = str(entry_ticker.get()).upper()  # 엔트리에 입력된 특정 종목 티커 받아오기
    stock = yf.Ticker(ticker)  # 주식 데이터 다운로드
    dividends = stock.dividends  # 역대 배당금 조회

    # 종가 데이터프레임 만들기
    df_price = stock.history(interval="1d", period="max")  # 특정 종목 정보 받아오기
    df_price = df_price.reset_index()  # 인덱스 초기화
    df_price["Year"] = (
        df_price["Date"].astype("str").str.split("-").str[0]
    )  # 연도 컬럼 생성

    # 종가 피벗 테이블 만들기
    df_pivot_price = pd.pivot_table(
        df_price, values="Close", index="Year", aggfunc="mean"
    )  # 같은 년도의 종가 평균가
    df_pivot_price = df_pivot_price.rename(
        columns={"Close": str(ticker + "_closed")}
    )  # 종가 피벗 테이블 컬럼명 바꾸기

    # 배당금 데이터프레임 만들기
    df_dividends = pd.DataFrame(dividends)  # 배당금 시리즈 -> 배당금 데이터프레임
    df_dividends = df_dividends.reset_index()  # 인덱스 초기화 -> 날짜 컬럼(Date) 생성
    df_dividends["Year"] = (
        df_dividends["Date"].astype("str").str.split("-").str[0]
    )  # 연도 컬럼 생성
    df_pivot_dividends = pd.pivot_table(
        df_dividends, values="Dividends", index="Year", aggfunc="sum"
    )  # 배당금 피벗 테이블 생성_연도별 배당금

    # 종가 테이블, 배당금 테이블 join 하기
    df_merged = pd.merge(
        left=df_pivot_price,
        right=df_pivot_dividends,
        left_index=True,
        right_index=True,
        how="inner",
    )  # 인덱스로 join 하기
    df_merged["Dividends yield rate"] = round(
        (df_merged["Dividends"] / df_merged[ticker + "_closed"]) * 100, 1
    )  # 배당률 컬럼 생성

    df_savefile = df_merged  # 저장할 데이터프레임 만들어 주기

    make_graph(df_merged, ticker)
```
\- 이번에 알게된건데, 함수 내부에서 global을 사용하지 않고 전역변수로 선언한 데이터프레임에 값을 넣어줄 경우, 함수 내부에서 호출할 때는 값이 잘 나타나지만, 밖에서 호출하면 빈 데이터프레임만 보인다.  

### 2-2-3. 시각화 함수
```
# 시각화 함수
def make_graph(df, ticker):
    for widget in frame_2.winfo_children():  # 그래프 매번 새로 그리기
        widget.destroy()

    # 한글 폰트 설정
    plt.rcParams["font.family"] = "Malgun Gothic"  # Windows의 맑은 고딕
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 그래프1
    ax1.set_xlabel("년도")  # 수정. x축 label
    ax1.set_ylabel("배당률", color="red")  # 수정. 그래프1 y축 label
    (line1,) = ax1.plot(
        df.index,
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
        df.index, df["Dividends"], label=ticker + "_배당금", color="blue"
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

    canvas_graph = FigureCanvasTkAgg(fig, frame_2)
    canvas_graph.get_tk_widget().pack(side=LEFT, fill=BOTH)
```

### 2-2-4. 저장 창 띄우기  
![image](https://github.com/user-attachments/assets/28f6cddb-a836-44bf-85ff-17106d049453)

```
def save_graph():  # 그래프 저장
    filename = filedialog.asksaveasfilename(
        initialfile="Untitled.png",
        defaultextension=".png",
        filetypes=[("All Files", "*.*"), ("Portable Graphics Format", "*.png")],
    )
    plt.savefig(filename)


def save_excelfile():  # 엑셀파일 저장
    filename = filedialog.asksaveasfilename(
        initialfile="Untitled.xlsx",
        defaultextension=".xlsx",
        filetypes=[("All Files", "*.*"), ("Excel 통합 문서", "*.xlsx")],
    )
    df_savefile.to_excel(filename, index=True, index_label="Year")
```    
\- 위 이미지처럼, 특정 버튼을 눌렀을 때 저장하는 창을 띄워주려면 filedialog.asksaveasfilename 를 사용해야 한다. (이것 또한 이번에 알게됨)  
\- 데이터프레임을 엑셀로 저장하든, 그래프를 이미지 파일로 저장하든, 저장할 때 경로를 입력하는 부분에 넣어주면 어디에 저장할 건지 선택하는 창을 띄워준다.  

### 2-2-5. GUI 부분
```
# 윈도우 생성
window = Tk()
window.title("Dividends Search")  # 윈도우 이름
window.geometry("1200x600")  # 윈도우 크기

# 프레임 생성
frame_1 = Frame(
    master=window, relief=RAISED
)  # 티커 검색 버튼, 엑셀 저장 버튼, 그래프 저장 버튼 프레임
frame_2 = Frame(master=window)  # 그래프 출력 프레임
# frame_3 = Frame(master=window) # 엑셀 파일 저장, 그래프 저장 프레임

# 레이블 위젯 : 티커를 입력하세요
label_ticker = Label(master=frame_1, text="Tiker : ", font=("Arial", 25))

# 엔트리 위젯 : 티커 입력. 테스트로는 x의 몇 제곱인지
entry_ticker = Entry(
    master=frame_1, fg="black", bg="white", width=20, justify=CENTER, font=("Arial", 25)
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

canvas_graph = FigureCanvasTkAgg(fig, frame_2)
canvas_graph.get_tk_widget().pack(side=LEFT, fill=BOTH)


frame_1.pack()
frame_2.pack()
# frame_3.pack()

label_ticker.pack(side=LEFT)
entry_ticker.pack(side=LEFT)

# 버튼 배치
button_search.pack(side=LEFT)
button_download_excel.pack(side=LEFT)
button_download_graph.pack(side=LEFT)

window.mainloop()
```
